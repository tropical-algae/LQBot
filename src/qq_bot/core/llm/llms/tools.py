from collections import defaultdict
import os
import ast
import asyncio
from pathlib import Path
from typing import Any, Optional
from itertools import chain

from openai.types.chat import ChatCompletionMessageToolCall
from qq_bot.utils.models import GroupMessageData
from qq_bot.core.llm.base import OpenAIBase
from llama_index.core.llms import ChatMessage, MessageRole

from qq_bot.utils.config import settings
from qq_bot.utils.logger import logger


class LLMToolbox(OpenAIBase):
    __model_tag__ = settings.TOOLS_LLM_CONFIG_NAME

    def __init__(
        self,
        base_url: str,
        api_key: str,
        prompt_path: str | Path,
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

    async def run(
        self, message: GroupMessageData, **kwargs
    ) -> list[ChatCompletionMessageToolCall] | None:
        if not self.active:
            return None
        
        content = [
            ChatMessage(content=f"消息发送者：{message.sender.nickname}\n当前时间：{message.get_time()}\n消息：{message.content}", role=MessageRole.USER)
        ]
        # messages = [f"[{m.sender.nickname or 'QQ用户'}][{m.send_time}]: '{m.content}'" for m in message]
        response = await self._async_inference(
            messages=content, tool_choice="auto", **kwargs
        )
        if response:
            return response.tool_calls
        return None
