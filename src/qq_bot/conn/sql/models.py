from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, String, Boolean, BIGINT, Integer
from sqlmodel import Field, SQLModel


class GroupMessageModel(SQLModel, table=True):
    __tablename__ = "group_message"

    id: Optional[int] = Field(
        default=None, sa_column=Column("id", BIGINT, primary_key=True)
    )
    group_id: int = Field(sa_column=Column("group_id", BIGINT, nullable=False))
    sender_id: int = Field(sa_column=Column("sender_id", BIGINT, nullable=False))
    message: str = Field(sa_column=Column("message", String(255), nullable=False))
    reply_to_id: Optional[int] = Field(
        default=None, sa_column=Column("reply_to_id", BIGINT)
    )
    receiver_id: Optional[int] = Field(
        default=None, sa_column=Column("receiver_id", BIGINT)
    )
    from_bot: bool = Field(sa_column=Column("from_bot", Boolean, nullable=False))
    create_time: datetime = Field(
        sa_column=Column("create_time", DateTime, nullable=False)
    )


class GroupQUserModel(SQLModel, table=True):
    __tablename__ = "group_quser"

    user_id: int = Field(sa_column=Column("user_id", BIGINT, primary_key=True))
    group_id: int = Field(sa_column=Column("group_id", BIGINT, nullable=False))
    is_valid: int = Field(sa_column=Column("is_valid", Boolean, nullable=False))


class QUserModel(SQLModel, table=True):
    __tablename__ = "quser"

    id: Optional[int] = Field(
        default=None, sa_column=Column("id", BIGINT, primary_key=True)
    )
    nickname: Optional[str] = Field(
        default=None, sa_column=Column("nickname", String(64))
    )
    card: Optional[str] = Field(
        default=None, sa_column=Column("card", String(255))
    )
    sex: Optional[str] = Field(default=None, sa_column=Column("sex", String(16)))
    age: Optional[int] = Field(default=None, sa_column=Column("age", Integer))

