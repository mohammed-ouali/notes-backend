from pydantic import BaseModel, Field
from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(description="Items on the current page.")
    total: int = Field(description="Total number of matching items across all pages.")
    page: int = Field(description="Current page number, starting from 1.")
    limit: int = Field(description="Maximum number of items requested per page.")