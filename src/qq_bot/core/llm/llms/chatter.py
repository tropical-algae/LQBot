from collections import defaultdict
from datetime import datetime
import os
import ast
import asyncio
from typing import Any, Optional
from itertools import chain
from qq_bot.core.llm.memory import MemoryManager
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.util_text import parse_text
from qq_bot.core.llm.base import OpenAIBase

from qq_bot.utils.config import settings
from qq_bot.utils.logger import logger

class LLMChatter(OpenAIBase):
    __model_tag__ = settings.CHATTER_LLM_CONFIG_NAME

    def __init__(
        self,
        base_url: str,
        api_key: str,
        prompt_path: str,
        max_retries: int = 3,
        retry: int = 3,
        **kwargs,
    ) -> None:
        super().__init__(
            base_url=base_url,
            api_key=api_key,
            prompt_path=prompt_path,
            max_retries=max_retries,
            retry=retry,
            **kwargs,
        )
        self.memory = MemoryManager(
            memory_size=self.configs.get("memory_size", 100),
            context_length=self.configs.get("context_length", 5),
            sys_prompt=self.system_prompt,
            message_template=self.message_template
        )

    def update_memory(
        self, 
        messages: GroupMessageRecord | list[GroupMessageRecord],
    ):
        self.memory.upsert(messages=messages)

    async def run(self, message: GroupMessageRecord, **kwargs) -> str | None:
        if not self.active:
            return self.default_reply
        
        self.update_memory(messages=message)
        memory: list = self.memory.load(message.group_id)
        llm_message = await self._async_inference(messages=memory, **kwargs)

        if llm_message and llm_message.raw:
            return llm_message.raw.choices[0].message.content
        return None
