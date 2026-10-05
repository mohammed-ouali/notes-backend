from __future__ import annotations

from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)


class UserBase(BaseModel):
    email: EmailStr = Field(description="Email address associated with the account.")


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password for the account.",
    )


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(
        ..., min_length=8, max_length=128,
        description="Current account password.",
    )
    new_password: str = Field(
        ..., min_length=8, max_length=128,
        description="Replacement account password; it must differ from the current password.",
    )

    @model_validator(mode="after")
    def validate_passwords_differ(self) -> ChangePasswordRequest:
        if self.old_password == self.new_password:
            raise ValueError("New password must be different from the old password.")
        return self


class UserResponse(UserBase):
    id: int = Field(description="Unique identifier of the account.")
    created_at: datetime = Field(description="Date and time the account was created.")
    is_active: bool = Field(description="Whether the account is active.")

    model_config = ConfigDict(from_attributes=True)