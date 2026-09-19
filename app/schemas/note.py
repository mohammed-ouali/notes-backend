from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class NoteBase(BaseModel):
    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )
    content: str | None = None

    @field_validator("title")
    @classmethod
    def validate_and_sanitize_title(cls, value: str) -> str:
        trimmed_value = value.strip()

        if not trimmed_value:
            raise ValueError("Note title cannot consist only of whitespace.")

        return trimmed_value

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return value.strip()


class NoteCreate(NoteBase):
    folder_id: int | None = Field(None, gt=0)


class NoteUpdate(BaseModel):
    title: str | None = Field(
        None,
        min_length=1,
        max_length=255,
    )
    content: str | None = None
    folder_id: int | None = Field(None, gt=0)

    @field_validator("title")
    @classmethod
    def validate_and_sanitize_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        trimmed_value = value.strip()

        if not trimmed_value:
            raise ValueError("Note title cannot consist only of whitespace.")

        return trimmed_value

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return value.strip()

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("Update payload cannot be empty.")

        return self


class NoteResponse(NoteBase):
    id: int
    user_id: int
    folder_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)