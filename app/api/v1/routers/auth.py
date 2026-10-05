from fastapi import Depends, status, APIRouter, BackgroundTasks
from app.api.dependencies.services import get_auth_service, get_email_service
from app.core.email import EmailService
from app.core.exceptions import ProblemDetails
from app.schemas.auth import LoginRequest, RefreshTokenRequest, Token
from app.schemas.user import UserCreate
from app.services.auth import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    summary="Register an account",
    description="Create an account and issue an access token and refresh token. Registration does not require authentication.",
    status_code=status.HTTP_201_CREATED,
    response_model=Token,
    response_description="The newly issued access and refresh tokens.",
    responses={
        409: {"model": ProblemDetails, "description": "An account with this email address already exists."},
        422: {"model": ProblemDetails, "description": "The request body failed validation."},
    },
)
async def register(
    user_data: UserCreate,
    background_tasks : BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends((get_email_service))
):
    token = await service.register_user(user_data)

    background_tasks.add_task(email_service.send_welcome_email, user_data.email)

    return token


@router.post(
    "/login",
    summary="Sign in",
    description="Authenticate with an account email address and password to receive an access token and refresh token.",
    response_model=Token,
    response_description="The issued access and refresh tokens.",
    responses={
        401: {"model": ProblemDetails, "description": "The email address or password is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        422: {"model": ProblemDetails, "description": "The request body failed validation."},
    },
)
async def login(
    credentials: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    
    return await service.login_user(
        email=credentials.email,
        password=credentials.password,
    )


@router.post(
    "/refresh",
    summary="Refresh tokens",
    description="Exchange a valid refresh token for a new access token and refresh token. This operation does not require an access token.",
    response_model=Token,
    response_description="The newly issued access and refresh tokens.",
    responses={
        401: {"model": ProblemDetails, "description": "The refresh token is invalid or expired."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        422: {"model": ProblemDetails, "description": "The request body failed validation."},
    },
)
async def refresh_token(
    body: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.refresh_tokens(body.refresh_token)