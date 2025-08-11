from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel
from ncatbot.core import BotAPI, GroupMessage

from qq_bot.conn.sql.models import GroupMessageModel, QUserModel


class QUserData(BaseModel):
    id: int
    nickname: str | None = None
    card: str | None = None
    sex: str | None = None
    age: int | None = None

    @classmethod
    async def from_group(
        cls,
        group_id: int,
        id: int | None = None,
        api: BotAPI | None = None,
    ) -> Union["QUserData", list["QUserData"], None]:
        if api is None:
            return None

        # 如果没有 nickname，就批量获取群成员
        if id is None:
            qusers: dict = await api.get_group_member_list(group_id, no_cache=False)
            if qusers and qusers.get("status") == "ok":
                return [
                    cls(
                        id=quser["user_id"],
                        nickname=quser["nickname"],
                        sex=quser["sex"],
                        age=quser["age"],
                        card=quser["card"]
                    )
                    for quser in qusers["data"]
                ]

        # 否则获取单个用户信息
        quser: dict = await api.get_group_member_info(group_id=group_id, user_id=id, no_cache=False)
        if quser and quser.get("status") == "ok":
            data = quser["data"]
            return cls(
                id=data["user_id"],
                nickname=data["nickname"],
                sex=data["sex"],
                age=data["age"],
                card=data["card"]
            )

        return None

    @classmethod
    def from_quser_model(cls, data: QUserModel | None) -> Optional["QUserData"]:
        return (
            cls(
                id=data.id,
                nickname=data.nickname,
                sex=data.sex,
                age=data.age,
                card=data.card,
            )
            if data
            else None
        )


class GroupMessageData(BaseModel):
    id: int
    content: str
    group_id: int
    sender: QUserData
    receiver: QUserData | None = None
    reply_to_id: int | None = None
    from_bot: bool
    send_time: datetime

    def get_time(self) -> str:
        return self.send_time.isoformat() # datetime.fromisoformat(self.send_time)

    @classmethod
    async def from_group_message(
        cls, data: GroupMessage, from_bot: bool, api: BotAPI | None = None
    ) -> "GroupMessageData":
        def get_data_from_message(message: list[dict], type: str) -> dict:
            return next(
                (item["data"] for item in message if item.get("type") == type),
                {},
            )

        content = get_data_from_message(data.message, "text").get("text", "").strip()
        reply_message_id = get_data_from_message(data.message, "reply").get("id", None)
        send_time = datetime.fromtimestamp(data.time).isoformat()
        sender_obj = await QUserData.from_group(
            id=int(data.sender.user_id),
            group_id=int(data.group_id),
            api=api,
        )
        receiver_obj = (
            await QUserData.from_group(id=int(receiver_id), group_id=data.group_id, api=api)
            if (receiver_id := get_data_from_message(data.message, "at").get("qq", None))
            else None
        )

        return cls(
            id=str(data.message_id),
            group_id=str(data.group_id),
            content=content,
            sender=sender_obj,
            receiver=receiver_obj,
            reply_message_id=reply_message_id,
            from_bot=from_bot,
            send_time=send_time,
        )

    @classmethod
    def from_group_message_model(
        cls, data: GroupMessageModel, sender: QUserModel, receiver: QUserModel | None = None
    ) -> "GroupMessageData":
        sender_obj = QUserData.from_quser_model(sender)
        receiver_obj = QUserData.from_quser_model(receiver) if receiver else None

        return cls(
            id = data.id,
            content = data.message,
            group_id = data.group_id,
            sender = sender_obj,
            receiver = receiver_obj,
            reply_to_id = data.reply_to_id,
            from_bot = data.from_bot,
            send_time = data.create_time
        )

    def to_group_message_model(self) -> GroupMessageModel:
        return GroupMessageModel(
            id=self.id,
            group_id=self.group_id,
            sender_id=self.sender.id,
            message=self.content,
            from_bot=self.from_bot,
            reply_to_id=self.reply_to_id,
            receiver_id=self.receiver.id if self.receiver else None,
            create_time=self.send_time
        )


class PrivateMessageRecord(BaseModel):
    id: str
    content: str
    sender_id: str


class EntityObject(BaseModel):
    id: str
    name: str
    attribute: str
    real_id: str  # 对于QQ用户实体，real id为QQ id

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, EntityObject) and self.id == other.id


class RelationObject(BaseModel):
    id: str
    name: str
    describe: str


class RelationTriplet(BaseModel):
    subject: EntityObject
    object: EntityObject
    relation: RelationObject
