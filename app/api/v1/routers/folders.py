from typing import Literal

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies.services import get_folder_service
from app.api.dependencies.auth import get_current_active_user
from app.schemas.folder import (
    FolderCreate,
    FolderResponse,
    FolderUpdate,
)
from app.schemas.note import NoteResponse
from app.schemas.pagination import PaginatedResponse
from app.models import User
from app.services.folder import FolderService


router = APIRouter(
    prefix="/folders",
    tags=["Folders"],
)


@router.get(
    "",
    response_model=PaginatedResponse[FolderResponse],
)
async def get_folders(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Items per page",
    ),
    q: str | None = Query(
        default=None,
        description="Search by folder name",
    ),
    sort_by: Literal[
        "created_at",
        "name",
    ] = Query(
        default="created_at",
        description="Field to sort by",
    ),
    order: Literal[
        "asc",
        "desc",
    ] = Query(
        default="asc",
        description="Sorting direction",
    ),
    current_user: User = Depends(
        get_current_active_user 
    ),
    service: FolderService = Depends(
        get_folder_service
    ),
):
    return await service.get_all_folders(
        page=page,
        limit=limit,
        q=q,
        sort_by=sort_by,
        order=order,
        user_id=current_user.id,
    )


@router.get(
    "/{folder_id}",
    response_model=FolderResponse,
)
async def get_folder(
    folder_id: int,
    current_user: User = Depends(
        get_current_active_user
    ),
    service: FolderService = Depends(
        get_folder_service
    ),
):
    return await service.get_folder_by_id(folder_id, user_id=current_user.id)


@router.get(
    "/{folder_id}/children",
    response_model=list[FolderResponse],
)
async def get_folder_children(
    folder_id: int,
    current_user: User = Depends(
        get_current_active_user
    ),
    service: FolderService = Depends(
        get_folder_service
    ),
):
    return await service.get_children(folder_id, user_id=current_user.id)


@router.get(
    "/{folder_id}/notes",
    response_model=PaginatedResponse[NoteResponse],
)
async def get_folder_notes(
    folder_id: int,
    page: int = Query(
        default=1,
        ge=1,
        description="Page number",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Items per page",
    ),
    current_user: User = Depends(
        get_current_active_user
    ),
    service: FolderService = Depends(
        get_folder_service
    ),
):
    return await service.get_folder_notes(
        folder_id=folder_id,
        page=page,
        limit=limit,
        user_id=current_user.id
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=FolderResponse,
)
async def create_folder(
    folder_data: FolderCreate,
    current_user: User = Depends(
        get_current_active_user
    ),
    service: FolderService = Depends(
        get_folder_service
    ),
):
    return await service.create_folder(folder_data, user_id=current_user.id)


@router.patch(
    "/{folder_id}",
    response_model=FolderResponse,
)
async def update_folder(
    folder_id: int,
    folder_data: FolderUpdate,
    current_user: User = Depends(
        get_current_active_user
    ),
    service: FolderService = Depends(
        get_folder_service
    ),
):
    return await service.update_folder(
        folder_id,
        folder_data,
        user_id=current_user.id
    )


@router.delete(
    "/{folder_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_folder(
    folder_id: int,
    current_user: User = Depends(
        get_current_active_user
    ),
    service: FolderService = Depends(
        get_folder_service
    ),
):
    await service.delete_folder(folder_id, user_id=current_user.id)