from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.deps import CurrentUser, Database
from app.models import Category
from app.schemas import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter()


def visible_categories(user_id: int):
    return select(Category).where((Category.is_default.is_(True)) | (Category.user_id == user_id))


@router.get("/", response_model=list[CategoryRead])
async def list_categories(user: CurrentUser, db: Database) -> list[Category]:
    return list((await db.scalars(visible_categories(user.id).order_by(Category.name))).all())


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(payload: CategoryCreate, user: CurrentUser, db: Database) -> Category:
    category = Category(name=payload.name, user_id=user.id, is_default=False)
    db.add(category)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A category with this name already exists") from exc
    await db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryRead)
async def get_category(category_id: int, user: CurrentUser, db: Database) -> Category:
    category = await db.scalar(visible_categories(user.id).where(Category.id == category_id))
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(category_id: int, payload: CategoryUpdate, user: CurrentUser, db: Database) -> Category:
    category = await db.scalar(select(Category).where(Category.id == category_id, Category.user_id == user.id, Category.is_default.is_(False)))
    if category is None:
        raise HTTPException(status_code=404, detail="Custom category not found")
    category.name = payload.name
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="A category with this name already exists") from exc
    await db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, user: CurrentUser, db: Database) -> None:
    category = await db.scalar(select(Category).where(Category.id == category_id, Category.user_id == user.id, Category.is_default.is_(False)))
    if category is None:
        raise HTTPException(status_code=404, detail="Custom category not found")
    await db.delete(category)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Category is used by existing expenses") from exc
