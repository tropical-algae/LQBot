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


class GroupMemory(BaseModel):
    group_id: int
    # 缓存的记忆长度
    memory_size: int
    # 上下文长度
    context_length: int
    # 群组id 对应的历史消息集合cache
    cache: list[list[GroupMessageRecord]] = []
    
    usr_cache: list[GroupMessageRecord] = []
    # 消息id 对应的模型回复消息
    llm_cache: OrderedDict[int, list[GroupMessageRecord]] = OrderedDict()
    
    def insert_msg(self, messages: list[GroupMessageRecord] | GroupMessageRecord) -> None:
        if not isinstance(messages, list):
            messages = [messages]
        
        temp_cache = []
        last_sender: str = ""
        for message in messages:
            if message.sender.id != last_sender:
                if temp_cache:
                    self.cache.append(deepcopy(temp_cache))
                    temp_cache.clear()
                last_sender = message.sender.id
            temp_cache.append(message)
        
        if temp_cache:
            self.cache.append(deepcopy(temp_cache))
    
    def get_msgs(self, message_template: str) -> list[ChatMessage]:
        result: list[ChatMessage] = []
        for msgs in self.cache[-self.context_length:]:
            for msg in msgs:
                role = MessageRole.ASSISTANT if msg.from_bot else MessageRole.ASSISTANT
                text = (
                    msg.content if msg.from_bot 
                    else message_template.format(**{
                        "text": msg.content,
                        "time": msg.send_time,
                        "sender": msg.sender.nikename or "None"
                    })
                )
                result.append(ChatMessage(content=text, role=role))
        result = result[-self.context_length * 3:]
        return result

class MemoryManager:

    def __init__(
        self, 
        memory_size: int, 
        context_length: int, 
        sys_prompt: str | ChatMessage,
        message_template: str,  # 用户message模板
    ):
        assert memory_size >= 0
        assert context_length > 0
        
        self.sys_prompt: ChatMessage = (
            sys_prompt if isinstance(sys_prompt, ChatMessage) 
            else ChatMessage(content=sys_prompt, role=MessageRole.SYSTEM)
        )
        self.message_template = message_template
        self.memory_size = memory_size
        self.context_length = context_length
        self._memories: dict[int, GroupMemory] = {}

    def _load_or_create_memory(self, group_id: int) -> GroupMemory:
        return self._memories.setdefault(
            group_id,
            GroupMemory(
                group_id=group_id,
                memory_size=self.memory_size,
                context_length=self.context_length,
            )
        )

    def load(self, group_id: int) -> list[ChatMessage]:
        memory = self._load_or_create_memory(group_id)
        messages: list[ChatMessage] = memory.get_msgs(self.message_template)
        messages.insert(0, self.sys_prompt)
        return messages

    def upsert(
        self,
        messages: GroupMessageRecord | list[GroupMessageRecord],
    ) -> None:
        if not messages:
            return
        
        group_id = messages.group_id if isinstance(messages, GroupMessageRecord) else messages[0].group_id
        memory = self._load_or_create_memory(group_id)
        memory.insert_msg(messages)

        record_messages(messages=messages)
