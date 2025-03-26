import os
import re
from functools import partial
from typing import Any, Optional, Union
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import (
    ChatCompletionUserMessageParam, 
    ChatCompletionAssistantMessageParam, 
    ChatCompletionSystemMessageParam
)
from qq_bot.basekit.util import function_retry, load_yaml


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
        **kwargs,
    ) -> None:
        assert os.path.isfile(prompt_path)
        
        self.retry = retry
        self.configs: dict = load_yaml(prompt_path)
        self._load_config()

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=20,
            **kwargs,
        )
        self.async_client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            max_retries=max_retries,
            timeout=20,
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
        prompts: dict = self.configs.get("prompts", {})

        self.default_model = self.configs.get("model", "gpt-3.5-turbo-ca")
        self.is_activate: bool = self.configs.get("activate", False)
        self.default_reply: str = self.configs.get("default_reply", "None")
        self.prompt: str = prompts.get(prompt_version, "")
        self.system_prompt = ChatCompletionSystemMessageParam(
            content=self.configs.get("system_prompt", "You are a helpful assistant."),
            role="user"
        )
        

    def _set_prompt(self, input: dict, prompt: str | None = None) -> str:
        def replacer(match, params: dict):
            var_name = match.group(1)
            return params.get(var_name, match.group(0))

        def standardization(params: Union[dict, str]) -> dict:
            params = {"data": params} if isinstance(input, str) else input
            return {k: str(v) for k, v in params.items()}

        params = standardization(input)
        pattern = re.compile(r"\$\{(\w+)\}")
        prompt = prompt if prompt else self.prompt
        return pattern.sub(partial(replacer, params=params), prompt)

    def format_user_message(self, content: str) -> ChatCompletionUserMessageParam:
        return ChatCompletionUserMessageParam(
            content=content,
            role="user"
        )
    
    def format_llm_message(self, content: str) -> ChatCompletionAssistantMessageParam:
        return ChatCompletionAssistantMessageParam(
            content=content, 
            role="assistant"
        )

    def _inference(self, content: str, model: Optional[str] = None, **kwargs) -> str:
        if self.is_activate:
            model = model or self.default_model

            messages = [ChatCompletionUserMessageParam(content=content, role="user")]
            completion = self.client.chat.completions.create(
                messages=messages, model=model, **kwargs  # type: ignore
            )
            if completion.choices and completion.choices[-1].message:
                response = completion.choices[-1].message.content
                if response:
                    return response
                return None
            return None
        else:
            return self.default_reply

    @function_retry
    async def _async_inference(self, content: Any, model: Optional[str] = None, **kwargs) -> str | None:
        if self.is_activate:
            assert isinstance(content, str) or isinstance(content, list), f"Illegal LLM input type: {type(content)}"

            model = model or self.default_model
            if isinstance(content, str):
                messages = [self.system_prompt, ChatCompletionUserMessageParam(content=content, role="user")]
            if isinstance(content, list):
                content.insert(0, self.system_prompt)
                messages=content

            completion = await self.async_client.chat.completions.create(messages=messages, model=model, temperature=0.4, **kwargs)
            if completion.choices and completion.choices[-1].message:
                response = completion.choices[-1].message.content
                if response:
                    return response
                return None
            return None
        else:
            return self.default_reply

    async def run(
        self, 
        message: Any,
        **kwargs
    ) -> Any:
        pass