from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings

# Keyed by client IP. Behind a reverse proxy, configure the proxy / uvicorn --proxy-headers
# so the real client IP is seen (Phase 13).
limiter = Limiter(key_func=get_remote_address, enabled=get_settings().rate_limit_enabled)
