from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from sqlalchemy import extract, func, select

from app.api.deps import CurrentUser, Database
from app.models import Category, Expense
from app.schemas import AnalyticsSummary, CategorySpending, MonthlySpending

router = APIRouter()


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + month - 1 + delta
    return index // 12, index % 12 + 1


@router.get("/summary", response_model=AnalyticsSummary)
async def summary(user: CurrentUser, db: Database, start_date: date, end_date: date) -> AnalyticsSummary:
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")
    base = select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.user_id == user.id)
    total = Decimal(await db.scalar(base.where(Expense.date >= start_date, Expense.date <= end_date)) or 0)
    duration = (end_date - start_date).days + 1
    previous_end = date.fromordinal(start_date.toordinal() - 1)
    previous_start = date.fromordinal(max(1, previous_end.toordinal() - duration + 1))
    previous_total = Decimal(await db.scalar(base.where(Expense.date >= previous_start, Expense.date <= previous_end)) or 0)
    grouped = await db.execute(select(Category.id, Category.name, func.sum(Expense.amount)).join(Category).where(Expense.user_id == user.id, Expense.date >= start_date, Expense.date <= end_date).group_by(Category.id, Category.name).order_by(Category.name))
    by_category = [CategorySpending(category_id=cid, category_name=name, amount=Decimal(amount), percentage=(Decimal(amount) * 100 / total).quantize(Decimal("0.01")) if total else Decimal("0.00")) for cid, name, amount in grouped.all()]
    month_query = await db.execute(select(extract("year", Expense.date), extract("month", Expense.date), func.sum(Expense.amount)).where(Expense.user_id == user.id, Expense.date >= start_date, Expense.date <= end_date).group_by(extract("year", Expense.date), extract("month", Expense.date)))
    month_totals = {(int(y), int(m)): Decimal(amount) for y, m, amount in month_query.all()}
    monthly: list[MonthlySpending] = []
    year, month = start_date.year, start_date.month
    while (year, month) <= (end_date.year, end_date.month):
        monthly.append(MonthlySpending(month=f"{year:04d}-{month:02d}", amount=month_totals.get((year, month), Decimal("0.00"))))
        year, month = shift_month(year, month, 1)
    change = ((total - previous_total) * 100 / previous_total).quantize(Decimal("0.01")) if previous_total else (Decimal("0.00") if not total else None)
    return AnalyticsSummary(start_date=start_date, end_date=end_date, total=total, by_category=by_category, monthly_trend=monthly, previous_period_total=previous_total, change_percentage=change)
