from typing import Any
import uuid
from copy import deepcopy

from pydantic import BaseModel
from collections import OrderedDict, defaultdict

from llama_index.core.llms import ChatMessage, MessageRole

from qq_bot.conn.sql.crud.group_message_crud import insert_group_message, insert_group_messages
from qq_bot.conn.sql.service import record_messages
from qq_bot.utils.decorator import sql_session
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.logger import logger
from qq_bot.utils.config import settings



class Memory(BaseModel):
    group_id: int
    # 缓存的记忆长度
    memory_size: int
    # 上下文长度
    context_length: int
    # 群组id 对应的历史消息集合cache
    usr_cache: list[GroupMessageRecord] = []
    # 消息id 对应的模型回复消息
    llm_cache: OrderedDict[int, list[GroupMessageRecord]] = OrderedDict()
    
    def get_msgs(self) -> list[ChatMessage]:
        result: list[ChatMessage] = []
        for u_msg in self.usr_cache[-self.context_length:]:
            result.append(ChatMessage(content=u_msg.content, role=MessageRole.USER))
            l_msg: GroupMessageRecord | None = self.llm_cache.get(u_msg.id, None)
            if l_msg:
                result.append(ChatMessage(content=l_msg.content, role=MessageRole.ASSISTANT))
        
        return result

    def insert_usr_msg(self, message: GroupMessageRecord) -> None:
        if len(self.usr_cache) >= self.memory_size:
            self.usr_cache.pop(0)
        self.usr_cache.append(message)
        
    def insert_llm_msg(self, messages: list[GroupMessageRecord]) -> None:
        if messages:
            replied_id = messages[0].reply_message_id
            if len(self.llm_cache) >= self.memory_size:
                self.llm_cache.popitem(last=False)
            self.llm_cache[replied_id] = messages

class MemoryManager:

    def __init__(self, memory_size: int, context_length: int, sys_prompt: str | ChatMessage):
        assert memory_size >= 0
        assert context_length > 0
        
        self.sys_prompt: ChatMessage = (
            sys_prompt if isinstance(sys_prompt, ChatMessage) 
            else ChatMessage(content=sys_prompt, role=MessageRole.SYSTEM)
        )
        self.memory_size = memory_size
        self.context_length = context_length
        self._memories: dict[int, Memory] = {}

    def _load_or_create_memory(self, group_id: int) -> Memory:
        return self._memories.setdefault(
            group_id,
            Memory(
                group_id=group_id,
                memory_size=self.memory_size,
                context_length=self.context_length,
            )
        )

    def load(self, group_id: int) -> list[ChatMessage]:
        memory = self._load_or_create_memory(group_id)
        messages: list[ChatMessage] = memory.get_msgs()
        messages.insert(0, self.sys_prompt)
        return messages

    def upsert(
        self,
        messages: GroupMessageRecord | list[GroupMessageRecord],
        from_user: bool,
    ) -> None:
        if not messages:
            return
        
        group_id = messages.group_id if isinstance(messages, GroupMessageRecord) else messages[0].group_id
        memory = self._load_or_create_memory(group_id)
        
        if from_user:
            memory.insert_usr_msg(messages)
        else:
            memory.insert_llm_msg(messages)

        record_messages(messages=messages)
