import os
import re
from functools import partial
from typing import Any, Optional, Union
from llama_index.core.llms import ChatMessage, CompletionResponse, ChatResponse

# from openai import AsyncOpenAI, OpenAI
# from openai.types.chat import (
#     ChatCompletionUserMessageParam,
#     ChatCompletionAssistantMessageParam,
#     ChatCompletionSystemMessageParam,
#     ChatCompletionMessage,
# )

from llama_index.llms.openai import OpenAI

from qq_bot.utils.util import load_yaml
from qq_bot.utils.decorator import function_retry
from qq_bot.utils.logger import logger


class OpenAIBase:
    __model_tag__ = "openai"
    _subclasses = []

    def __init__(
        self,
        base_url: str,
        api_key: str,
        prompt_path: str,
        max_retries: int = 3,
        retry: int = 3,
        timeout: int = 60,
        **kwargs,
    ) -> None:
        # assert os.path.isfile(prompt_path)

        self.retry = retry
        self.configs: dict = load_yaml(prompt_path)
        self._load_config()
        
        self.client = OpenAI(
            api_key=api_key,
            api_base=base_url,
            max_retries=max_retries,
            timeout=timeout,
            **kwargs,
        )


    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        OpenAIBase._subclasses.append(cls)

    @classmethod
    def subclasses(cls):
        return cls._subclasses

    def _load_config(self):
        prompt_version = self.configs.get("version", "v1")

        self.default_model = self.configs.get("model", "gpt-3.5-turbo-ca")
        self.active: bool = self.configs.get("active", False)
        self.default_reply: str = self.configs.get("default_reply", "None")
        self.prompt: str = self.configs.get("prompts", {}).get(prompt_version, "")
        self.system_prompt = ChatMessage(
            content=(
                self.configs.get("system_prompt", {}).get(
                    prompt_version, "You are a helpful assistant."
                )
            ),
            role="system",
        )

    def _set_prompt(self, prompt: str | None = None, **kwargs) -> str:
        template = prompt if prompt else self.prompt
        template = template.format(**kwargs)
        return template

    @function_retry
    async def _async_inference(self, messages: list[ChatMessage], **kwargs) -> CompletionResponse | ChatResponse | None:
        model = kwargs.pop("model", None) or self.default_model

        logger.info(messages)
        completion = (
            await self.client.acomplete(prompt=messages[0].content, model=model, **kwargs)
            if len(messages) == 1
            else await self.client.achat(messages=messages, model=model, **kwargs)
        )

        return completion

    async def run(self, message: Any, **kwargs) -> Any:
        pass
