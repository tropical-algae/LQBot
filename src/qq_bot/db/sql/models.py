from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Index, Integer
from sqlalchemy.dialects.mysql import VARCHAR
from sqlmodel import Field, SQLModel

class GroupBotMessage(SQLModel, table=True):
    __tablename__ = 'group_bot_message'
    __table_args__ = (
        Index('group_bot_chat_id', 'id', unique=True),
        Index('group_bot_message_reply_id', 'reply_msg_id')
    )

    id: Optional[str] = Field(default=None, sa_column=Column('id', VARCHAR(256), primary_key=True))
    reply_msg_id: str = Field(sa_column=Column('reply_msg_id', VARCHAR(256), nullable=False))
    group_id: str = Field(sa_column=Column('group_id', VARCHAR(64), nullable=False))
    message: str = Field(sa_column=Column('message', VARCHAR(255), nullable=False))
    create_time: datetime = Field(sa_column=Column('create_time', DateTime, nullable=False))


class GroupChatMessage(SQLModel, table=True):
    __tablename__ = 'group_chat_message'
    __table_args__ = (
        Index('group_chat_id', 'id', unique=True),
        Index('group_chat_message_type_id', 'type_id')
    )

    id: Optional[str] = Field(default=None, sa_column=Column('id', VARCHAR(256), primary_key=True))
    type_id: int = Field(sa_column=Column('type_id', Integer, nullable=False))
    group_id: str = Field(sa_column=Column('group_id', VARCHAR(64), nullable=False))
    sender_id: str = Field(sa_column=Column('sender_id', VARCHAR(64), nullable=False))
    message: str = Field(sa_column=Column('message', VARCHAR(255), nullable=False))
    create_time: datetime = Field(sa_column=Column('create_time', DateTime, nullable=False))


class GroupQueryRecordRelation(SQLModel, table=True):
    __tablename__ = 'group_query_record_relation'
    __table_args__ = (
        Index('group_relation_query_id', 'query_id'),
        Index('group_relation_record_id', 'record_id')
    )

    id: Optional[str] = Field(default=None, sa_column=Column('id', VARCHAR(32), primary_key=True))
    query_id: str = Field(sa_column=Column('query_id', VARCHAR(256), nullable=False))
    record_id: str = Field(sa_column=Column('record_id', VARCHAR(256), nullable=False))
    score: float = Field(sa_column=Column('score', Float, nullable=False))


class MessageType(SQLModel, table=True):
    __tablename__ = 'message_type'

    id: Optional[int] = Field(default=None, sa_column=Column('id', Integer, primary_key=True))
    name: str = Field(sa_column=Column('name', VARCHAR(255), nullable=False))
