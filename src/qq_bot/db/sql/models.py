from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.mysql import TINYINT
from sqlmodel import Field, SQLModel

class OfficialGroupBotMessage(SQLModel, table=True):
    __tablename__ = 'official_group_bot_message'
    __table_args__ = (
        Index('group_bot_chat_id', 'id', unique=True),
        Index('group_bot_message_reply_id', 'reply_msg_id')
    )

    id: Optional[str] = Field(default=None, sa_column=Column('id', String(256), primary_key=True))
    reply_msg_id: str = Field(sa_column=Column('reply_msg_id', String(256), nullable=False))
    group_id: str = Field(sa_column=Column('group_id', String(64), nullable=False))
    message: str = Field(sa_column=Column('message', String(255), nullable=False))
    create_time: datetime = Field(sa_column=Column('create_time', DateTime, nullable=False))


class OfficialGroupChatMessage(SQLModel, table=True):
    __tablename__ = 'official_group_chat_message'
    __table_args__ = (
        Index('group_chat_id', 'id', unique=True),
        Index('group_chat_message_type_id', 'type_id')
    )

    id: Optional[str] = Field(default=None, sa_column=Column('id', String(256), primary_key=True))
    type_id: int = Field(sa_column=Column('type_id', Integer, nullable=False))
    group_id: str = Field(sa_column=Column('group_id', String(64), nullable=False))
    sender_id: str = Field(sa_column=Column('sender_id', String(64), nullable=False))
    message: str = Field(sa_column=Column('message', String(255), nullable=False))
    create_time: datetime = Field(sa_column=Column('create_time', DateTime, nullable=False))


class OfficialGroupQueryRecordRelation(SQLModel, table=True):
    __tablename__ = 'official_group_query_record_relation'
    __table_args__ = (
        Index('group_relation_query_id', 'query_id'),
        Index('group_relation_record_id', 'record_id')
    )

    id: Optional[str] = Field(default=None, sa_column=Column('id', String(32), primary_key=True))
    query_id: str = Field(sa_column=Column('query_id', String(256), nullable=False))
    record_id: str = Field(sa_column=Column('record_id', String(256), nullable=False))
    score: float = Field(sa_column=Column('score', Float, nullable=False))


class OfficialMessageType(SQLModel, table=True):
    __tablename__ = 'official_message_type'

    id: Optional[int] = Field(default=None, sa_column=Column('id', Integer, primary_key=True))
    name: str = Field(sa_column=Column('name', String(255), nullable=False))


class UnofficialGroupMessageV1(SQLModel, table=True):
    __tablename__ = 'unofficial_group_message_v1'

    id: Optional[str] = Field(default=None, sa_column=Column('id', String(32), primary_key=True))
    group_id: str = Field(sa_column=Column('group_id', String(32), nullable=False))
    sender_id: str = Field(sa_column=Column('sender_id', String(32), nullable=False))
    message: str = Field(sa_column=Column('message', String(255), nullable=False))
    is_bot: int = Field(sa_column=Column('is_bot', TINYINT(1), nullable=False))
    create_time: datetime = Field(sa_column=Column('create_time', DateTime, nullable=False))
    reply_message_id: Optional[str] = Field(default=None, sa_column=Column('reply_message_id', String(32)))
    at_user_id: Optional[str] = Field(default=None, sa_column=Column('at_user_id', String(32)))
