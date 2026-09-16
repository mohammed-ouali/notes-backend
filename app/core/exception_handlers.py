from fastapi import status
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from loguru import logger

from app.core.exceptions import (
    ProblemDetails,
    DomainException,
    DOMAIN_EXCEPTION_MAP
)


async def domain_exception_handler(
        request: Request, exception: DomainException
) -> JSONResponse:
    status_code, title = DOMAIN_EXCEPTION_MAP.get(
        type(exception), DOMAIN_EXCEPTION_MAP[DomainException]
        )

    problem = ProblemDetails(
        type="about:blank",
        title=title,
        status=status_code,
        detail=exception.message,
        instance=request.url.path
    )

    headers = {}

    if status_code == 401:
        headers["WWW-Authenticate"] = "Bearer"

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(problem),
        media_type="application/problem+json",
        headers=headers
    )


async def validation_exception_handler(
        request: Request,
        exception: RequestValidationError
) -> JSONResponse:
    invalid_params = [
        {
        "name": "->".join(str(loc) for loc in error["loc"]),
        "reason": error["msg"]
        } 
        for error in exception.errors()
    ]

        
    problem = ProblemDetails(
        type="about:blank",
        title="Validation Error",
        status=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail="The request body or parameters failed validation.",
        instance=request.url.path,
        invalid_params=invalid_params,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=jsonable_encoder(problem),
        media_type="application/problem+json",
    )


async def unhandled_exception_handler(
        request: Request, exception: Exception
) -> JSONResponse:

    logger.exception(f"Unhandled exception on {request.url.path}")

    problem = ProblemDetails(
        type="about:blank",
        title="Internal Server Error",
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred.",
        instance=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=jsonable_encoder(problem),
        media_type="application/problem+json",
    )