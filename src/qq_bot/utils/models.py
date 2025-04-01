from datetime import datetime
from pydantic import BaseModel
from ncatbot.core import BotAPI, GroupMessage

from qq_bot.conn.sql.models import UserV1
from qq_bot.utils.util_text import trans_int, trans_str

class QUser(BaseModel):
    id: int
    nikename: str | None = None
    sex: str | None = None
    age: int | None = None
    long_nick: str | None = None
    
    @classmethod
    async def from_group(
        cls, 
        id: int, 
        group_id: int,
        nikename: str | None = None,
        api: BotAPI | None = None, 
    ) -> type["QUser"]:
        if api and (at_user_info := await api.get_group_member_info(
            group_id=group_id, 
            user_id=id, 
            no_cache=False
        )) and at_user_info["status"] == "ok":
            return cls(
                id=at_user_info["data"]["user_id"],
                nikename=at_user_info["data"]["nikename"],
                sex=at_user_info["data"]["sex"],
                age=at_user_info["data"]["age"],
            )
        return cls(id=id, nikename=nikename)
    
    @classmethod
    async def from_sql_model(
        cls, 
        data: UserV1 | None
    ) -> type["QUser"]:
        return cls(
            id=trans_int(data.id),
            nikename=data.nikename,
            sex=data.sex,
            age=data.age,
            long_nick=data.long_nick
        ) if data else None


class GroupMessageRecord(BaseModel):
    id: int
    content: str
    group_id: int
    sender: QUser
    at_user: QUser | None = None
    reply_message_id: int | None = None
    from_bot: bool
    send_time: str
    
    def get_datetime(self) -> datetime:
        return datetime.fromisoformat(self.send_time)
    
    def str_id(self) -> str:
        return str(self.id)
    
    def str_group_id(self) -> str:
        return str(self.group_id)
    
    def str_sender_id(self) -> str:
        return str(self.sender.id)
    
    def str_reply_message_id(self) -> str | None:
        return trans_str(self.reply_message_id)
    
    def str_at_user_id(self) -> str | None:
        return str(self.at_user.id) if self.at_user else None

    
    @classmethod
    async def from_group_message(
        cls, 
        data: GroupMessage,
        from_bot: bool,
        api: BotAPI | None = None
    ) -> type["GroupMessageRecord"]:
        def get_data_from_message(message: list[dict], type: str) -> dict:
            return next((item["data"] for item in message if item.get("type") == type), {})
        
        content = get_data_from_message(data.message, "text").get("text", "").strip()
        reply_message_id = get_data_from_message(data.message, "reply").get("id", None)
        send_time = datetime.fromtimestamp(data.time).isoformat()
        sender = await QUser.from_group(
            id=int(data.sender.user_id), 
            group_id=int(data.group_id), 
            nikename=str(data.sender.nickname), 
            api=api
        )
        at_user = (
            await QUser.from_group(id=int(at_user_id), group_id=data.group_id, api=api) 
            if (at_user_id := get_data_from_message(data.message, "at").get("qq", None)) 
            else None
        )
        
        return cls(
            id=str(data.message_id),
            group_id=str(data.group_id),
            content=content,
            sender=sender,
            at_user=at_user,
            reply_message_id=reply_message_id,
            from_bot=from_bot,
            send_time=send_time
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
