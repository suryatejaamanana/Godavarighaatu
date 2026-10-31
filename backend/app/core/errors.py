from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = 404


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
