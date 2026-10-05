from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, status

from app.api.dependencies.services import get_folder_service
from app.api.dependencies.auth import get_current_active_user
from app.core.exceptions import ProblemDetails
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
    summary="List folders",
    description="Return a paginated list of folders owned by the authenticated user, with optional name search and sorting.",
    response_model=PaginatedResponse[FolderResponse],
    response_description="A page of matching folders.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        422: {"model": ProblemDetails, "description": "A query parameter failed validation."},
    },
)
async def get_folders(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number, starting from 1.",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of folders to return per page.",
    ),
    q: str | None = Query(
        default=None,
        description="Search folders by name.",
    ),
    sort_by: Literal[
        "created_at",
        "name",
    ] = Query(
        default="created_at",
        description="Folder field used to sort the results.",
    ),
    order: Literal[
        "asc",
        "desc",
    ] = Query(
        default="asc",
        description="Sort direction for the results.",
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
    summary="Get a folder",
    description="Retrieve a folder owned by the authenticated user.",
    response_model=FolderResponse,
    response_description="The requested folder.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The folder could not be found."},
        422: {"model": ProblemDetails, "description": "The folder ID failed validation."},
    },
)
async def get_folder(
    folder_id: int = Path(description="Unique identifier of the folder."),
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
    summary="List child folders",
    description="List the immediate child folders of a folder owned by the authenticated user.",
    response_model=list[FolderResponse],
    response_description="The folder's immediate child folders.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The parent folder could not be found."},
        422: {"model": ProblemDetails, "description": "The folder ID failed validation."},
    },
)
async def get_folder_children(
    folder_id: int = Path(description="Unique identifier of the parent folder."),
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
    summary="List notes in a folder",
    description="Return a paginated list of notes in a folder owned by the authenticated user.",
    response_model=PaginatedResponse[NoteResponse],
    response_description="A page of notes in the folder.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The folder could not be found."},
        422: {"model": ProblemDetails, "description": "The folder ID or a query parameter failed validation."},
    },
)
async def get_folder_notes(
    folder_id: int = Path(description="Unique identifier of the folder."),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number, starting from 1.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of notes to return per page.",
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
    summary="Create a folder",
    description="Create a folder for the authenticated user, optionally within one of their existing folders.",
    status_code=status.HTTP_201_CREATED,
    response_model=FolderResponse,
    response_description="The created folder.",
    responses={
        400: {"model": ProblemDetails, "description": "The requested parent would create an invalid folder hierarchy."},
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The selected parent folder could not be found."},
        409: {"model": ProblemDetails, "description": "A folder with this name already exists in the same parent folder."},
        422: {"model": ProblemDetails, "description": "The request body failed validation."},
    },
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
    summary="Update a folder",
    description="Update the name or parent of a folder owned by the authenticated user.",
    response_model=FolderResponse,
    response_description="The updated folder.",
    responses={
        400: {"model": ProblemDetails, "description": "The requested parent would create an invalid folder hierarchy."},
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The folder or selected parent folder could not be found."},
        409: {"model": ProblemDetails, "description": "A folder with this name already exists in the same parent folder."},
        422: {"model": ProblemDetails, "description": "The request body failed validation."},
    },
)
async def update_folder(
    folder_id: Annotated[int, Path(description="Unique identifier of the folder.")],
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
    summary="Delete a folder",
    description="Delete a folder owned by the authenticated user.",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The folder was deleted successfully.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The folder could not be found."},
        422: {"model": ProblemDetails, "description": "The folder ID failed validation."},
    },
)
async def delete_folder(
    folder_id: int = Path(description="Unique identifier of the folder."),
    current_user: User = Depends(
        get_current_active_user
    ),
    service: FolderService = Depends(
        get_folder_service
    ),
):
    await service.delete_folder(folder_id, user_id=current_user.id)