from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlmodel import Field, SQLModel


class GroupMessageV1(SQLModel, table=True):
    __tablename__ = "group_message_v1"

    id: Optional[str] = Field(
        default=None, sa_column=Column("id", String(32), primary_key=True)
    )
    group_id: str = Field(sa_column=Column("group_id", String(32), nullable=False))
    sender_id: str = Field(sa_column=Column("sender_id", String(32), nullable=False))
    message: str = Field(sa_column=Column("message", String(255), nullable=False))
    from_bot: int = Field(sa_column=Column("from_bot", Boolean, nullable=False))
    create_time: datetime = Field(
        sa_column=Column("create_time", DateTime, nullable=False)
    )
    reply_message_id: Optional[str] = Field(
        default=None, sa_column=Column("reply_message_id", String(32))
    )
    at_user_id: Optional[str] = Field(
        default=None, sa_column=Column("at_user_id", String(32))
    )


class UserGroupV1(SQLModel, table=True):
    __tablename__ = "user_group_v1"

    user_id: int = Field(sa_column=Column("user_id", Integer, primary_key=True))
    group_id: int = Field(sa_column=Column("group_id", Integer, nullable=False))
    is_valid: int = Field(sa_column=Column("is_valid", Boolean, nullable=False))


class UserV1(SQLModel, table=True):
    __tablename__ = "user_v1"

    id: Optional[str] = Field(
        default=None, sa_column=Column("id", String(32), primary_key=True)
    )
    nikename: Optional[str] = Field(
        default=None, sa_column=Column("nikename", String(64))
    )
    sex: Optional[str] = Field(default=None, sa_column=Column("sex", String(16)))
    age: Optional[int] = Field(default=None, sa_column=Column("age", Integer))
    long_nick: Optional[str] = Field(
        default=None, sa_column=Column("long_nick", String(255))
    )
