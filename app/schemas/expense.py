from datetime import date as Date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExpenseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    description: str = Field(min_length=1, max_length=1000, strip_whitespace=True)
    date: Date
    category_id: int = Field(gt=0)


class ExpenseUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")
    description: str | None = Field(default=None, min_length=1, max_length=1000, strip_whitespace=True)
    date: Date | None = None
    category_id: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def reject_empty_patch(self) -> "ExpenseUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be supplied")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("Supplied fields cannot be null")
        return self


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int
    amount: Decimal
    currency: str
    description: str
    date: Date
    category_id: int
