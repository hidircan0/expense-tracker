from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CategorySpending(BaseModel):
    category_id: int
    category_name: str
    amount: Decimal
    percentage: Decimal


class MonthlySpending(BaseModel):
    month: str
    amount: Decimal


class AnalyticsSummary(BaseModel):
    start_date: date
    end_date: date
    total: Decimal
    by_category: list[CategorySpending]
    monthly_trend: list[MonthlySpending]
    previous_period_total: Decimal
    change_percentage: Decimal | None
