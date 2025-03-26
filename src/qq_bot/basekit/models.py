from datetime import datetime
from pydantic import BaseModel


class GroupMessageRecord(BaseModel):
    id: str
    content: str
    group_id: str
    sender_id: str
    create_time: str
    
    def get_datetime(self) -> datetime:
        return datetime.fromisoformat(self.create_time)


class PrivateMessageRecord(BaseModel):
    id: str
    content: str
    sender_id: str

