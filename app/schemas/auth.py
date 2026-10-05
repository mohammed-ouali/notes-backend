from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr = Field(description="Email address registered to the account.")
    password: str = Field(
            ...,
            min_length=8,
            max_length=128,
            description="Account password.",
        )

class Token(BaseModel):
    access_token: str = Field(description="Bearer token for accessing protected resources.")
    refresh_token: str = Field(description="Token used to obtain a refreshed token pair.")
    token_type: str = Field(default="bearer", description="Token type used in the Authorization header.")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(description="Refresh token issued by the authentication API.")

