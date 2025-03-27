from collections import defaultdict
import os
import ast
import asyncio
from typing import Any, Optional
from itertools import chain
from qq_bot.basekit.models import GroupMessageRecord
from qq_bot.basekit.util import parse_text
from qq_bot.service.llm_server.llms.base import OpenAIBase

from qq_bot.basekit.config import settings
from qq_bot.basekit.logging import logger


class LLMChatter(OpenAIBase):
    __model_tag__ = settings.LLM_CAHT_CONFIG_NAME

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
            result.append(self.format_user_message(u_msg))
            
            l_msg = self.llm_cache.get(u_msg, None)
            if l_msg:
                result.append(self.format_llm_message(l_msg))
        return result

    def insert_and_update_history_message(
        self, 
        group_id: str, 
        user_message: str, 
        llm_message: str | None = None
    ) -> None:
        group_user_cache: list = self.user_cache[group_id]
        if len(group_user_cache) >= self.cache_len:
            removed_msg = group_user_cache.pop(0)
            self.llm_cache.pop(removed_msg, None)
        group_user_cache.append(user_message)

        self.user_cache[group_id] = group_user_cache
        if llm_message:
            self.llm_cache[user_message] = llm_message

    def reduce_token(chatbot, system, context, myKey):
        context.append({"role": "user", "content": "请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。在总结中不要加入这一句话。"})

        response = None # get_response(system, context, myKey, raw=True)

        statistics = f'本次对话Tokens用量【{response["usage"]["completion_tokens"]+12+12+8} / 4096】'
        optmz_str = parse_text( f'好的，我们之前聊了:{response["choices"][0]["message"]["content"]}\n\n================\n\n{statistics}' )
        chatbot.append(("请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。", optmz_str))

        context = []
        context.append({"role": "user", "content": "我们之前聊了什么?"})
        context.append({"role": "assistant", "content": f'我们之前聊了：{response["choices"][0]["message"]["content"]}'})
        return chatbot, context

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
