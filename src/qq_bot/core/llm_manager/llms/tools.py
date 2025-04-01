from collections import defaultdict
import os
import ast
import asyncio
from typing import Any, Optional
from itertools import chain

from openai.types.chat import ChatCompletionMessageToolCall
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.core.llm_manager.llms.base import OpenAIBase

from qq_bot.utils.config import settings
from qq_bot.utils.logging import logger


class LLMToolbox(OpenAIBase):
    __model_tag__ = settings.TOOLS_LLM_CONFIG_NAME

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

    async def run(
        self, 
        message: GroupMessageRecord,
        **kwargs
    ) -> list[ChatCompletionMessageToolCall] | None:
        content = f"消息发送者：{message.sender.nikename}\n当前时间：{message.send_time}\n消息：{message.content}"
        # messages = [f"[{m.sender.nikename or 'QQ用户'}][{m.send_time}]: '{m.content}'" for m in message]
        response = await self._async_inference(content=content, tool_choice="auto", **kwargs)
        if response:
            return response.tool_calls
        return None
                
        # if response:
        #     response_parsed: list = extract_json_from_markdown(response)
        #     if len(response_parsed) > 0:
        #         triplets: list[dict] = response_parsed[-1]
        #         logger.info(f"[{self.__model_tag__}]: 抽取实体关系共[{len(triplets)}组 -> {str(triplets)}")
        #         return triplets

        #     logger.info(f"[{self.__model_tag__}]: 实体解析失败 -> 文本未匹配")

        # logger.info(f"[{self.__model_tag__}]: 模型推理失败")
