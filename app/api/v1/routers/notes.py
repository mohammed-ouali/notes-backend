from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Path, status, UploadFile, File
from fastapi.responses import StreamingResponse

from app.api.dependencies.services import get_note_service, get_attachment_service
from app.api.dependencies.auth import get_current_active_user
from app.core.config import settings
from app.core.exceptions import ProblemDetails
from app.models import User

from app.schemas.note import (
    NoteCreate,
    NoteResponse,
    NoteUpdate,
)
from app.schemas.attachment import AttachmentResponse
from app.schemas.pagination import PaginatedResponse
from app.services.note import NoteService
from app.services.attachment import AttachmentService


router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
)


@router.get(
    "",
    summary="List notes",
    description="Return a paginated list of notes owned by the authenticated user, with optional search, sorting, and folder filtering.",
    response_model=PaginatedResponse[NoteResponse],
    response_description="A page of matching notes.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The requested folder could not be found."},
        422: {"model": ProblemDetails, "description": "A query parameter failed validation."},
    },
)
async def get_notes(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number, starting from 1.",
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of notes to return per page.",
    ),
    q: str | None = Query(
        default=None,
        description="Search notes by title or content.",
    ),
    sort_by: Literal["created_at", "updated_at"] = Query(
        default="created_at",
        description="Note field used to sort the results.",
    ),
    order: Literal["asc", "desc"] = Query(
        default="asc",
        description="Sort direction for the results.",
    ),
    folder_id: int | None = Query(
        default=None,
        description="Return only notes in this folder.",
    ),
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    return await service.get_all_notes(
        page=page,
        limit=limit,
        q=q,
        sort_by=sort_by,
        order=order,
        folder_id=folder_id,
        user_id=current_user.id,
    )


@router.get(
    "/{note_id}",
    summary="Get a note",
    description="Retrieve a note owned by the authenticated user.",
    response_model=NoteResponse,
    response_description="The requested note.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The note could not be found."},
        422: {"model": ProblemDetails, "description": "The note ID failed validation."},
    },
)
async def get_note(
    note_id: int = Path(description="Unique identifier of the note."),
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    return await service.get_note_by_id(note_id=note_id, user_id=current_user.id)


@router.post(
    "",
    summary="Create a note",
    description="Create a note for the authenticated user, optionally placing it in one of their folders.",
    status_code=status.HTTP_201_CREATED,
    response_model=NoteResponse,
    response_description="The created note.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The selected folder could not be found."},
        422: {"model": ProblemDetails, "description": "The request body failed validation."},
    },
)
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    return await service.create_note(note_data=note_data, user_id=current_user.id)


@router.put(
    "/{note_id}",
    summary="Update a note",
    description="Replace the supplied fields of a note owned by the authenticated user.",
    response_model=NoteResponse,
    response_description="The updated note.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The note or selected folder could not be found."},
        422: {"model": ProblemDetails, "description": "The request body failed validation."},
    },
)
async def update_note(
    note_id: Annotated[int, Path(description="Unique identifier of the note.")],
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    return await service.update_note(
        note_id=note_id,
        note_data=note_data,
        user_id=current_user.id,
    )


@router.delete(
    "/{note_id}",
    summary="Delete a note",
    description="Delete a note owned by the authenticated user.",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The note was deleted successfully.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The note could not be found."},
        422: {"model": ProblemDetails, "description": "The note ID failed validation."},
    },
)
async def delete_note(
    note_id: int = Path(description="Unique identifier of the note."),
    current_user: User = Depends(get_current_active_user),
    service: NoteService = Depends(get_note_service),
):
    await service.delete_note(
        note_id=note_id, 
        user_id=current_user.id
    )


@router.get(
    "/{note_id}/attachments",
    summary="List note attachments",
    description="List the attachments belonging to a note owned by the authenticated user.",
    response_model=list[AttachmentResponse],
    response_description="The note's attachments.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The note could not be found."},
        422: {"model": ProblemDetails, "description": "The note ID failed validation."},
    },
)
async def get_attachments(
    note_id: int = Path(description="Unique identifier of the note."),
    current_user: User = Depends(get_current_active_user),
    service: AttachmentService = Depends(get_attachment_service)
):
    return await service.get_all_attachments_by_note(
        user_id=current_user.id, 
        note_id=note_id
        )


@router.get(
    "/{note_id}/attachments/{attachment_id}",
    summary="Download an attachment",
    description="Download an attachment belonging to a note owned by the authenticated user.",
    response_class=StreamingResponse,
    response_description="The attachment file, returned with its stored media type.",
    responses={
        200: {
            "description": "Attachment file contents.",
            "content": {
                "image/png": {"schema": {"type": "string", "format": "binary"}},
                "image/jpeg": {"schema": {"type": "string", "format": "binary"}},
                "application/pdf": {"schema": {"type": "string", "format": "binary"}},
            },
        },
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The note or attachment could not be found."},
        422: {"model": ProblemDetails, "description": "A note or attachment ID failed validation."},
    },
)
async def get_attachment(
    note_id: int = Path(description="Unique identifier of the note."),
    attachment_id: int = Path(description="Unique identifier of the attachment."),
    current_user: User = Depends(get_current_active_user),
    service: AttachmentService = Depends(get_attachment_service)
):
    attachment, stream = await service.get_attachment_by_id(
        user_id=current_user.id, 
        note_id=note_id, 
        attachment_id=attachment_id
    )

    return StreamingResponse(
        content=stream,
        media_type=attachment.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{attachment.file_name}"'
        },
    )


@router.post(
    "/{note_id}/attachments",
    summary="Upload an attachment",
    description=(
        "Upload a PNG, JPEG, or PDF attachment to a note owned by the authenticated user. "
        f"The required multipart file must not exceed {settings.max_attachment_size_bytes} bytes; "
        f"the combined attachment size for the note must not exceed {settings.max_note_attachments_size_bytes} bytes."
    ),
    status_code=status.HTTP_201_CREATED,
    response_model=AttachmentResponse,
    response_description="The uploaded attachment's metadata.",
    responses={
        400: {"model": ProblemDetails, "description": "The file type is unsupported or its content does not match its declared media type."},
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The note could not be found."},
        413: {"model": ProblemDetails, "description": "The file or combined note attachment size exceeds its configured limit."},
        422: {"model": ProblemDetails, "description": "The multipart request or required file field failed validation."},
    },
)
async def upload_attachment(
    note_id: int = Path(description="Unique identifier of the note."),
    file: UploadFile = File(
        ...,
        description=(
            "Required file to upload. Supported media types are image/png, image/jpeg, "
            "and application/pdf."
        ),
    ),
    current_user: User = Depends(get_current_active_user),
    service: AttachmentService = Depends(get_attachment_service)
):
    return await service.upload_attachment(
        user_id=current_user.id, 
        note_id=note_id, 
        file=file
    )


@router.delete(
    "/{note_id}/attachments/{attachment_id}",
    summary="Delete an attachment",
    description="Delete an attachment belonging to a note owned by the authenticated user.",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The attachment was deleted successfully.",
    responses={
        401: {"description": "Authentication is required or the access token is invalid."},
        403: {"model": ProblemDetails, "description": "The account is inactive."},
        404: {"model": ProblemDetails, "description": "The note or attachment could not be found."},
        422: {"model": ProblemDetails, "description": "A note or attachment ID failed validation."},
    },
)
async def delete_attachment(
    note_id: int = Path(description="Unique identifier of the note."),
    attachment_id: int = Path(description="Unique identifier of the attachment."),
    current_user: User = Depends(get_current_active_user),
    service: AttachmentService = Depends(get_attachment_service)
):
    await service.delete_attachment(
        user_id=current_user.id, 
        note_id=note_id, 
        attachment_id=attachment_id
    )