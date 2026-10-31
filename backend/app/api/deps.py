from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError


def require_admin() -> None:
    """Single swap-point for admin protection.

    Phase 5 replaces this with real JWT authentication and role checks.
    Until then admin routes only work when APP_ENV=development and are refused otherwise,
    so they can never be exposed unprotected by accident.
    """
    if get_settings().app_env != "development":
        raise ServiceUnavailableError("Admin API is disabled until authentication is implemented.")
