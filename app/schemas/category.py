from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80, strip_whitespace=True)


class CategoryUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80, strip_whitespace=True)


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: int
    name: str
    is_default: bool
