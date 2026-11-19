from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select

from app.api.deps import CurrentUser, Database
from app.models import Category, Expense
from app.schemas import ExpenseCreate, ExpenseRead, ExpenseUpdate

router = APIRouter()


async def ensure_visible_category(category_id: int, user_id: int, db: Database) -> None:
    category = await db.scalar(select(Category).where(Category.id == category_id, (Category.is_default.is_(True)) | (Category.user_id == user_id)))
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")


def owned_expense(expense_id: int, user_id: int):
    return select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id)


@router.post("/", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
async def create_expense(payload: ExpenseCreate, user: CurrentUser, db: Database) -> Expense:
    await ensure_visible_category(payload.category_id, user.id, db)
    expense = Expense(**payload.model_dump(), user_id=user.id)
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return expense


@router.get("/", response_model=list[ExpenseRead])
async def list_expenses(
    user: CurrentUser, db: Database, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
    start_date: date | None = None, end_date: date | None = None, category_id: int | None = Query(None, gt=0),
    min_amount: Decimal | None = Query(None, gt=0), max_amount: Decimal | None = Query(None, gt=0),
) -> list[Expense]:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(status_code=422, detail="min_amount must not exceed max_amount")
    query = select(Expense).where(Expense.user_id == user.id)
    if start_date:
        query = query.where(Expense.date >= start_date)
    if end_date:
        query = query.where(Expense.date <= end_date)
    if category_id:
        query = query.where(Expense.category_id == category_id)
    if min_amount is not None:
        query = query.where(Expense.amount >= min_amount)
    if max_amount is not None:
        query = query.where(Expense.amount <= max_amount)
    return list((await db.scalars(query.order_by(Expense.date.desc(), Expense.id.desc()).offset(skip).limit(limit))).all())


@router.get("/{expense_id}", response_model=ExpenseRead)
async def get_expense(expense_id: int, user: CurrentUser, db: Database) -> Expense:
    expense = await db.scalar(owned_expense(expense_id, user.id))
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@router.patch("/{expense_id}", response_model=ExpenseRead)
async def update_expense(expense_id: int, payload: ExpenseUpdate, user: CurrentUser, db: Database) -> Expense:
    expense = await db.scalar(owned_expense(expense_id, user.id))
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    updates = payload.model_dump(exclude_unset=True)
    if "category_id" in updates:
        await ensure_visible_category(updates["category_id"], user.id, db)
    for key, value in updates.items():
        setattr(expense, key, value)
    await db.commit()
    await db.refresh(expense)
    return expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(expense_id: int, user: CurrentUser, db: Database) -> Response:
    expense = await db.scalar(owned_expense(expense_id, user.id))
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    await db.delete(expense)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
