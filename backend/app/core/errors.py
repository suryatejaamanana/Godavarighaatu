from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


class UnauthorizedError(AppError):
    status_code = 401


class ForbiddenError(AppError):
    status_code = 403


class ConflictError(AppError):
    status_code = 409


class BusinessRuleError(AppError):
    status_code = 422


class ServiceUnavailableError(AppError):
    status_code = 503


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse({"detail": exc.message}, status_code=exc.status_code)

    @app.exception_handler(IntegrityError)
    async def _integrity(_: Request, exc: IntegrityError) -> JSONResponse:
        # Safety net: services check conflicts first, the DB constraints are the final guard.
        return JSONResponse(
            {"detail": "The request conflicts with existing data."}, status_code=409
        )

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limited(_: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            {"detail": "Too many requests. Please try again later."},
            status_code=429,
            headers={"Retry-After": "60"},
        )
