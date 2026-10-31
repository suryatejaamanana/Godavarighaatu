from typing import Annotated

from fastapi import Depends, Request

from app.core.config import get_settings
from app.core.db import DB
from app.core.errors import ForbiddenError, UnauthorizedError
from app.models import Admin
from app.models.enums import AdminRole
from app.services import auth as auth_service

ACCESS_COOKIE = "gg_access"
REFRESH_COOKIE = "gg_refresh"

ROLE_RANK = {AdminRole.STAFF: 1, AdminRole.MANAGER: 2, AdminRole.SUPER_ADMIN: 3}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def check_csrf(request: Request) -> None:
    """Cookie-authenticated state-changing requests must come from an allowed origin.

    Browsers always send Origin on cross-origin and non-GET fetches; SameSite cookies are the
    first line of defence and this is the second. Non-browser clients must send a matching Origin.
    """
    if request.method in SAFE_METHODS:
        return
    if request.headers.get("origin") not in get_settings().cors_origins:
        raise ForbiddenError("Request origin is not allowed.")


def current_admin(request: Request, db: DB) -> Admin:
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise UnauthorizedError("Not authenticated.")
    check_csrf(request)
    return auth_service.authenticate_access_token(db, token)


CurrentAdmin = Annotated[Admin, Depends(current_admin)]


def require_role(minimum: AdminRole):
    """Roles are ranked staff < manager < super_admin; `minimum` and above are allowed."""

    def dependency(admin: CurrentAdmin) -> Admin:
        if ROLE_RANK[admin.role] < ROLE_RANK[minimum]:
            raise ForbiddenError("You do not have permission to perform this action.")
        return admin

    return dependency


require_staff = require_role(AdminRole.STAFF)
require_manager = require_role(AdminRole.MANAGER)
require_super_admin = require_role(AdminRole.SUPER_ADMIN)
