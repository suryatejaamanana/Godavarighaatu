from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.errors import ServiceUnavailableError


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    url = get_settings().database_url
    if not url:
        raise ServiceUnavailableError("Database is not configured.")
    return sessionmaker(create_engine(url, pool_pre_ping=True), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with get_session_factory()() as session:
        yield session


DB = Annotated[Session, Depends(get_db)]
