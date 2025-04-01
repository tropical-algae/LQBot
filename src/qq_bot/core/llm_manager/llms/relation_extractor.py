from collections import defaultdict
import os
import ast
import asyncio
from typing import Any, Optional
from itertools import chain
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.util_text import extract_json_from_markdown
from qq_bot.core.llm_manager.llms.base import OpenAIBase

from qq_bot.utils.config import settings
from qq_bot.utils.logging import logger


class LLMRelationExtractor(OpenAIBase):
    __model_tag__ = settings.RELATION_EXTOR_LLM_CONFIG_NAME

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
        message: list[GroupMessageRecord],
        **kwargs
    ) -> list[dict]:
        
        # messages = [f"[{m.sender.nikename or 'QQ用户'}][{m.send_time}]: '{m.content}'" for m in message]
        messages = message
        content = [self.format_user_message(self._set_prompt(input={"text": "\n".join(messages)}))]
        response = await self._async_inference(content=content, **kwargs)
        if response and response.content:
            response_parsed: list = extract_json_from_markdown(response.content)
            if len(response_parsed) > 0:
                triplets: list[dict] = response_parsed[-1]
                logger.info(f"[{self.__model_tag__}]: 抽取实体关系共[{len(triplets)}组 -> {str(triplets)}")
                return triplets

            logger.info(f"[{self.__model_tag__}]: 实体解析失败 -> 文本未匹配")

        logger.info(f"[{self.__model_tag__}]: 模型推理失败")
        return []
