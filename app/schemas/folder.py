from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FolderBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Name of the folder.",
    )

    @field_validator("name")
    @classmethod
    def validate_and_sanitize_name(cls, value: str) -> str:
        trimmed_value = value.strip()
        if not trimmed_value:
            raise ValueError("Folder name cannot consist solely of whitespace.")
        return trimmed_value


class FolderCreate(FolderBase):
    parent_id: int | None = Field(
        None, gt=0, description="ID of the parent folder, if this is a nested folder."
    )


class FolderUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128, description="Updated folder name.")
    parent_id: int | None = Field(
        None, gt=0, description="ID of the new parent folder, or null to make this a top-level folder."
    )

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
    id: int = Field(description="Unique identifier of the folder.")
    user_id: int = Field(description="Identifier of the folder's owner.")
    parent_id: int | None = Field(description="Identifier of the parent folder, if any.")
    created_at: datetime = Field(description="Date and time the folder was created.")
    updated_at: datetime = Field(description="Date and time the folder was last updated.")

    model_config = ConfigDict(from_attributes=True)