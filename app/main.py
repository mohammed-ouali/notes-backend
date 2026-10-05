from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.exceptions import DomainException
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.storage import Storage
from app.api.v1.router import api_router
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.security import SecurityHeadersMiddleware
from app.core.exception_handlers import (
    domain_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)

setup_logging()

storage = Storage()
storage.create_bucket_if_not_exists()

app = FastAPI(
    title=settings.app_name,
    description=(
        "A REST API for managing notes, folders, and file attachments, with "
        "account registration and token-based authentication. Protected "
        "resources require authentication."
    ),
    version=settings.api_version,
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Register accounts, sign in, and refresh access tokens.",
        },
        {
            "name": "Users",
            "description": "View and manage the authenticated user's account.",
        },
        {
            "name": "Notes",
            "description": "Create, find, and manage notes and their attachments.",
        },
        {
            "name": "Folders",
            "description": "Organize notes in folders and nested folders.",
        },
    ],
    debug=settings.debug
)

@app.get("/", summary="Check API availability", description="Confirm that the API is running.")
async def root():
    return {"message": "API is running"}

app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix="/api/v1")

