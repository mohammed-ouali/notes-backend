from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FolderBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Folder name must be between 1 and 128 characters long.",
    )

    @field_validator("name")
    @classmethod
    def validate_and_sanitize_name(cls, value: str) -> str:
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("Folder name cannot consist solely of whitespace.")
        return trimmed_value


class FolderCreate(FolderBase):
    parent_id: int | None = Field(None, gt=0)


class FolderUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    parent_id: int | None = Field(None, gt=0)

    @field_validator("name")
    @classmethod
    def validate_and_sanitize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("Folder name cannot consist solely of whitespace.")
        return trimmed_value

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> FolderUpdate:
        if self.name is None and self.parent_id is None:
            raise ValueError("Update payload cannot be empty.")
        return self


class FolderResponse(FolderBase):
    id: int
    user_id: int
    parent_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)