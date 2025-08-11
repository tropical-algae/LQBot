from copy import deepcopy

from pydantic import BaseModel

from llama_index.core.llms import ChatMessage, MessageRole

from qq_bot.conn.sql.service import load_messages, record_messages
from qq_bot.utils.models import GroupMessageData
from qq_bot.utils.logger import logger
from qq_bot.utils.config import settings


class GroupMemory(BaseModel):
    group_id: int
    # 缓存的记忆长度
    memory_size: int
    # 上下文长度
    context_length: int
    # 群组id 对应的历史消息集合cache
    cache: list[list[GroupMessageData]] = []
    
    def insert_msg(self, messages: list[GroupMessageData] | GroupMessageData) -> None:
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
                        "time": msg.get_time(),
                        "sender": msg.sender.nickname or "None"
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

    def init_memories(self):
        self._memories.clear()
        group_messages: dict[str, list[GroupMessageData]] = load_messages(count=self.memory_size)
        for group_id, messages in group_messages.items():
            memory = self._load_or_create_memory(int(group_id))
            memory.insert_msg(messages)
        logger.info(f"Init memory, load messages from sql -> {self._memories}")

    def load(self, group_id: int) -> list[ChatMessage]:
        memory = self._load_or_create_memory(group_id)
        messages: list[ChatMessage] = memory.get_msgs(self.message_template)
        messages.insert(0, self.sys_prompt)
        return messages

    def upsert(
        self,
        messages: GroupMessageData | list[GroupMessageData],
    ) -> None:
        if not messages:
            return
        
        group_id = messages.group_id if isinstance(messages, GroupMessageData) else messages[0].group_id
        memory = self._load_or_create_memory(group_id)
        memory.insert_msg(messages)

        record_messages(messages=messages)
