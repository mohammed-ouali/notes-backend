from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.services import get_user_service
from app.core.exceptions import ProblemDetails
from app.models import User
from app.schemas.user import ChangePasswordRequest, UserResponse
from app.services.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    summary="Get the current user's profile",
    description="Retrieve the profile of the authenticated user.",
    response_model=UserResponse,
    response_description="The authenticated user's profile.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The authenticated account could not be found."},
    },
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    return current_user



@router.post(
    "/me/change-password",
    summary="Change the current user's password",
    description="Change the authenticated user's password by providing the current password and a different replacement password.",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The password was changed successfully.",
    responses={
        400: {"model": ProblemDetails, "description": "The current password is incorrect."},
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The authenticated account could not be found."},
        422: {"model": ProblemDetails, "description": "The request body failed validation."},
    },
)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    await service.change_password(
        user_id=current_user.id,
        old_password=body.old_password,
        new_password=body.new_password,
    )


@router.delete(
    "/me",
    summary="Delete the current user's account",
    description="Delete the authenticated user's account.",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The account was deleted successfully.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The authenticated account could not be found."},
    },
)
async def delete_current_user_account(
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    await service.delete_user(user_id=current_user.id)