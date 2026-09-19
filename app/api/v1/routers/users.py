from fastapi import APIRouter, Depends, status

from app.api.dependencies.auth import get_current_active_user
from app.api.dependencies.services import get_user_service
from app.models import User
from app.schemas.user import ChangePasswordRequest, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    return await service.update_user(
        user_id=current_user.id,
        user_data=user_data,
    )


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
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
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_current_user_account(
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    await service.delete_user(user_id=current_user.id)