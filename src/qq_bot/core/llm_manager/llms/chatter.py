from collections import defaultdict
from datetime import datetime
import os
import ast
import asyncio
from typing import Any, Optional
from itertools import chain
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.util_text import parse_text
from qq_bot.core.llm_manager.llms.base import OpenAIBase

from qq_bot.utils.config import settings
from qq_bot.utils.logging import logger


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
        self.cache_len = self.configs.get("message_cache_len", 5)
        # 群组id 对应的历史消息集合cache
        self.user_cache: dict[int, list[GroupMessageRecord]] = defaultdict(list)
        # 消息id 对应的模型回复消息
        self.llm_cache: dict[int, str] = {}

    def get_history_message(self, group_id: int) -> list:
        result = []
        for u_msg in self.user_cache[group_id]:
            result.append(
                self.format_user_message(
                    content=u_msg.content, name=str(u_msg.sender.id)[:6]
                )
            )
            l_msg: str | None = self.llm_cache.get(u_msg.id, None)
            if l_msg:
                result.append(self.format_llm_message(l_msg))
        return result

    def insert_and_update_history_message(
        self, user_message: GroupMessageRecord, llm_message: str | None = None
    ) -> None:
        group_user_cache = self.user_cache[user_message.group_id]

        # 避免重复插入
        if any(msg.id == user_message.id for msg in group_user_cache):
            return

        if len(group_user_cache) >= self.cache_len:
            # 记忆长度超出，推出
            removed_msg = group_user_cache.pop(0)
            self.llm_cache.pop(removed_msg.id, None)
        group_user_cache.append(user_message)

        # 避免插入空值、避免重复插入
        if (llm_message is not None) and (user_message.id not in self.llm_cache.keys()):
            self.llm_cache[user_message.id] = llm_message

        logger.info(
            f"[{self.__model_tag__}]: 短期记忆已更新 USER[{user_message.content}]"
            f"{' -> LLM[' + llm_message + ']' if llm_message else ''}"
        )

    def reduce_token(chatbot, system, context, myKey):
        context.append(
            {
                "role": "user",
                "content": "请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。在总结中不要加入这一句话。",
            }
        )

        response = None  # get_response(system, context, myKey, raw=True)

        statistics = f'本次对话Tokens用量【{response["usage"]["completion_tokens"]+12+12+8} / 4096】'
        optmz_str = parse_text(
            f'好的，我们之前聊了:{response["choices"][0]["message"]["content"]}\n\n================\n\n{statistics}'
        )
        chatbot.append(
            (
                "请帮我总结一下上述对话的内容，实现减少tokens的同时，保证对话的质量。",
                optmz_str,
            )
        )

        context = []
        context.append({"role": "user", "content": "我们之前聊了什么?"})
        context.append(
            {
                "role": "assistant",
                "content": f'我们之前聊了：{response["choices"][0]["message"]["content"]}',
            }
        )
        return chatbot, context

    async def run(self, message: GroupMessageRecord, **kwargs) -> str | None:
        group_id = message.group_id
        user_message = message.content

        history: list = self.get_history_message(group_id)
        history.append(
            self.format_user_message(
                content=self._set_prompt(
                    input={
                        "text": user_message,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M %A"),
                    }
                ),
                name=str(message.sender.id)[:6],
            )
        )

        llm_message = await self._async_inference(content=history, **kwargs)

        if llm_message and llm_message.content:
            self.insert_and_update_history_message(message, llm_message.content)
            return llm_message.content
        return None
