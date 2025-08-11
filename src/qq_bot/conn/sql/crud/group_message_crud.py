from collections import defaultdict
import uuid
from sqlmodel import Session, select, func
from typing import Literal
from sqlalchemy.orm import aliased
from qq_bot.utils.models import GroupMessageData
from qq_bot.conn.sql.models import GroupMessageModel


def insert_group_message(
    db: Session,
    message: GroupMessageData,
) -> None:
    new_msg = message.to_group_message_model()
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)


def insert_group_messages(
    db: Session,
    messages: list[GroupMessageData],
) -> None:
    db.bulk_insert_mappings(
        GroupMessageModel,
        [
            message.to_group_message_model().model_dump()
            for message in messages
        ],
    )
    db.commit()


def select_current_group_messages(db: Session, count: int = 10) -> dict[str, list[GroupMessageModel]]:
    row_number = func.row_number().over(
        partition_by=GroupMessageModel.group_id,
        order_by=GroupMessageModel.create_time.desc()
    ).label("row_number")

    subq = (
        select(GroupMessageModel, row_number)
        .subquery()
    )

    gm_alias = aliased(GroupMessageModel, subq)

    stmt = (
        select(gm_alias)
        .where(subq.c.row_number <= count)
        .order_by(gm_alias.group_id, gm_alias.create_time.desc())
    )
    query_set = db.exec(stmt).all()
    result: dict[str, list[GroupMessageModel]] = defaultdict(list)
    
    # 反转顺序，按时间升序（最近的在列表最后）
    for qs in query_set:
        result[qs.group_id].insert(0, qs)

    return result
