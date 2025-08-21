from typing import Annotated

from lqbot.core.agent.base import AgentBase, ToolBase
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage


class MemoryResetTool(ToolBase):
    __tool_name__ = "memory_reset_tool"
    __tool_description__ = "清除历史对话记录"
    __is_async__ = False

    @staticmethod
    def tool_function() -> str:
        return "已清理历史记忆"

    @staticmethod
    async def a_tool_post_processing_function(
        agent: AgentBase, agent_message: AgentMessage
    ) -> None:
        session_id: str = agent_message.session_id
        await agent.reset_memory(session_id)
        logger.info(f"[GROUP {session_id}] 调用记忆清理工具")
