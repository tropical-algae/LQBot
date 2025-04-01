# import uuid
# from sqlmodel import Session, select
# from typing import Literal
# from qq_bot.utils.models import GroupMessageRecord
# from qq_bot.conn.sql.crud.ofcl_message_type_crud import get_message_type_id_by_name
# from qq_bot.conn.sql.models import OfficialGroupBotMessage, OfficialGroupChatMessage, OfficialGroupQueryRecordRelation, OfficialMessageType


# # _msg_type_cache: LRUCache[str, str] = LRUCache(maxsize=2048 * 10)

# # @cached(_msg_type_cache, key=lambda db, name: str(hashkey(name)))  # noqa
# # def get_message_type_id_by_name(db: Session, name: str) -> str | None:
# #     result = db.exec(select(MessageType.id).where(MessageType.name == name)).first()
# #     return str(result) if result else None


# def insert_user_group_message(
#     db: Session, 
#     message: GroupMessageRecord, 
#     type: Literal["聊天", "悄悄话", "询问"]
# ) -> None:
#     # 定义映射字典，将 type 映射到对应的模型类
#     msg_type_id = get_message_type_id_by_name(db=db, name=type)
#     if msg_type_id:
#         new_msg = OfficialGroupChatMessage(
#             id=message.id,
#             type_id=msg_type_id,
#             group_id=message.group_id,
#             sender_id=message.sender.id,
#             message=message.content,
#             create_time=message.get_datetime(),
#         )
#         db.add(new_msg)
#         db.commit()
#         db.refresh(new_msg)


# def insert_bot_group_message(
#     db: Session, 
#     message: GroupMessageRecord, 
#     user_msg_id: str
# ) -> None:
#     new_msg = OfficialGroupBotMessage(
#         id=message.id,
#         reply_msg_id=user_msg_id,
#         group_id=message.group_id,
#         message=message.content,
#         create_time=message.get_datetime()
#     )
#     db.add(new_msg)
#     db.commit()
#     db.refresh(new_msg)


# def insert_query_reocrd_relation(
#     db: Session, 
#     query_id: str, 
#     record_ids: list[str],
#     scores: list[float]
# ) -> None:
#     relations = [
#         OfficialGroupQueryRecordRelation(
#             id=uuid.uuid4().hex,
#             query_id=query_id,
#             record_id=record_id,
#             score=score
#         )
#         for record_id, score in zip(record_ids, scores)
#     ]
#     db.add_all(relations)
#     db.commit()
#     for relation in relations:
#         db.refresh(relation)

# # with LocalSession() as db:

# # insert_insert_message()