from typing import Any

from llama_index.core.tools import FunctionTool, QueryEngineTool, ToolMetadata
from pydantic import BaseModel

from lqbot.utils.models import AgentMessage


class InformationBase(BaseModel):
    def summary(self) -> str:
        return ""


class ToolBase:
    __tool_name__: str = ""
    __tool_description__: str = ""
    __is_async__: bool = False

    @staticmethod
    def tool_function(*args, **kwargs) -> Any:
        pass

    @staticmethod
    async def a_tool_function(*args, **kwargs) -> Any:
        pass

    @staticmethod
    def tool_post_processing_function(agent_message: AgentMessage) -> Any:
        pass

    @staticmethod
    async def a_tool_post_processing_function(agent_message: AgentMessage) -> Any:
        pass

    @classmethod
    def get_tool(cls) -> Any:
        return FunctionTool.from_defaults(
            name=cls.__tool_name__,
            description=cls.__tool_description__,
            fn=cls.tool_function if not cls.__is_async__ else None,
            async_fn=cls.a_tool_function if cls.__is_async__ else None,
        )
