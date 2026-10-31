import enum

from sqlalchemy import Enum


def str_enum(enum_cls: type[enum.StrEnum], name: str) -> Enum:
    """Store enum values as VARCHAR + CHECK (not native PG enums) so values are easy to migrate."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda e: [m.value for m in e],
        length=32,
    )
