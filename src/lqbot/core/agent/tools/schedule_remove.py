from collections.abc import Awaitable, Callable
from typing import Annotated, Any

from llama_index.core.tools import FunctionTool

from lqbot.core.agent.base import AgentBase, ToolBase
from lqbot.core.agent.tools.schedule import ScheduleInfo
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage


class ScheduleRemoveTool(ToolBase):
    __tool_name__ = "schedule_cleaner"
    __tool_description__ = "清除定时任务"
    __is_async__ = False
    plugin_function: Callable[..., ScheduleInfo | None] | None = None

    @staticmethod
    def tool_function(
        task_id: Annotated[str, "任务ID"],
    ) -> str:
        try:
            if ScheduleRemoveTool.plugin_function is None:
                logger.warning("定时器暂时无法使用")
                return "定时器暂时无法使用"

            schedule_info = ScheduleRemoveTool.plugin_function(task_id=task_id)
            return (
                f"以下任务已移除：\n{schedule_info.summary()}"
                if schedule_info
                else "定时任务未找到"
            )
        except Exception as err:
            logger.error(f"Schedule Error: {err}")
            return "清除定时任务时出现了一个错误！"

    @staticmethod
    def tool_post_processing_function(
        agent: AgentBase, agent_message: AgentMessage
    ) -> Any:
        _ = agent
        agent_message.can_split = False

    @classmethod
    def get_tool(cls) -> Any:
        return FunctionTool.from_defaults(
            name=cls.__tool_name__,
            description=cls.__tool_description__,
            fn=cls.tool_function if not cls.__is_async__ else None,
            async_fn=cls.a_tool_function if cls.__is_async__ else None,
            return_direct=True,
        )
