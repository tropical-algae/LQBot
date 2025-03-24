from collections import defaultdict
from copy import deepcopy
from typing import Optional
from openai.types.chat import (
    ChatCompletionUserMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionAssistantMessageParam
)

from qq_bot.common.logging import logger
from qq_bot.common.models import GroupMessageRecord
from qq_bot.service.chat_gpt.base import OpenAIBase
from qq_bot.common.config import settings


class ChitChatGPT(OpenAIBase):
    def __init__(self, base_url, api_key, prompt_path, default_model, max_retries = 3, cache_len: int = 4, **kwargs):
        super().__init__(base_url, api_key, prompt_path, default_model, max_retries, **kwargs)
        self.cache_len = cache_len * 2
        self.sys_msg = ChatCompletionSystemMessageParam(
            content=self.raw_instruct["system_message"],
            role="system"
        )
        self.group_chat_cache: dict[str, list] = defaultdict(list)
    
    def load_group_chat_cache(self, content: str, group_id: str) -> list:
        result = deepcopy(self.group_chat_cache[group_id])
        # result.insert(0, self.sys_msg)
        result.append(ChatCompletionUserMessageParam(content=content, role="user"))
        return result
    
    def save_group_chat_cache(self, current_msg: GroupMessageRecord, output: str) -> None:
        group_id = current_msg.group_id
        self.group_chat_cache[group_id].extend([
            ChatCompletionUserMessageParam(content=current_msg.content, role="user"),
            ChatCompletionAssistantMessageParam(content=output, role="assistant")
        ])
        
        if len(self.group_chat_cache[group_id]) > self.cache_len:
            self.group_chat_cache[group_id].pop(0)
            self.group_chat_cache[group_id].pop(0)
    
    async def run_group(self, message: GroupMessageRecord, model: Optional[str] = None, **kwargs) -> str:
        logger.info(f"[ChitChat] User input: {message.content}")
        content = self._set_prompt({"data": message.content})
        contents: list = self.load_group_chat_cache(content=content, group_id=message.group_id)
        logger.debug(f"[ChitChat] Total input: {contents}")
        output = await self._async_inference(content=contents, model=model, **kwargs)
        logger.info(f"[ChitChat] GPT output: {output}")

        self.save_group_chat_cache(current_msg=message, output=output)
        return output


chit_chat_gpt = ChitChatGPT(
    base_url=settings.GPT_BASE_URL,
    api_key=settings.GPT_API_KEY,
    prompt_path=settings.CHIT_CHAT_GPT_PROMPT,
    default_model=settings.GPT_DEFAULT_MODEL
)
