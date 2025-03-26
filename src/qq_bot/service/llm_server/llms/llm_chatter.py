from collections import defaultdict
import os
import ast
import asyncio
from typing import Any, Optional
from itertools import chain
from qq_bot.basekit.models import GroupMessageRecord
from qq_bot.service.llm_server.llms.base import OpenAIBase

from qq_bot.basekit.config import settings
from qq_bot.basekit.logging import logger


class LLMChatter(OpenAIBase):
    __model_tag__ = "bot_chatter"

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
            **kwargs
        )
        self.cache_len = self.configs.get("message_cache_len", 5)
        self.user_cache: dict[str, list] = defaultdict(list)
        self.llm_cache: dict[str, str] = {}

    def get_history_message(self, group_id: str) -> list:
        result = []
        for u_msg in self.user_cache[group_id]:
            l_msg = self.llm_cache.get(u_msg, "")
            result.extend([self.format_user_message(u_msg), self.format_llm_message(l_msg)])
        return result

    def insert_and_update_history_message(self, group_id: str, user_message: str, llm_message: str) -> None:
        group_user_cache: list = self.user_cache[group_id]
        if len(group_user_cache) >= self.cache_len:
            removed_msg = group_user_cache.pop(0)
            self.llm_cache.pop(removed_msg, None)
        group_user_cache.append(user_message)

        self.user_cache[group_id] = group_user_cache
        self.llm_cache[user_message] = llm_message

    async def run(
        self, 
        message: GroupMessageRecord,
        **kwargs
    ) -> str | None:
        group_id = message.group_id
        user_message = message.content

        history: list = self.get_history_message(group_id)
        history.append(self.format_user_message(self._set_prompt(input={"text": user_message})))

        llm_message = await self._async_inference(content=history, **kwargs)

        if llm_message:
            self.insert_and_update_history_message(group_id, user_message, llm_message)
            logger.info(f"[{self.__model_tag__}]: USER[{user_message}] -> LLM[{llm_message}]")

        return llm_message
