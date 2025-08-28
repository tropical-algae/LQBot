import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from dateutil import parser
from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from ncatbot.plugin import BasePlugin
from pydantic import BaseModel

from lqbot.core.agent.base import AgentBase, InformationBase, ToolBase
from lqbot.utils.config import settings
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage

schedule_queue: asyncio.Queue = asyncio.Queue()


class ReminderType(str, Enum):
    GITHUB_TREND = "推送github趋势"
    SUPER_EARTH_STATUS = "推送超级地球新闻"
    MESSAGE = "提醒事件或消息"


class Recurrence(str, Enum):
    DAILY = "每天"
    ONCE = "仅一次"


class ScheduleInfo(InformationBase):
    recurrence: Recurrence
    content: str
    date: str
    reminder_type: ReminderType
    session_id: str | None = None

    def summary(self, **kwargs) -> str:
        _ = kwargs
        return f"## 定时任务\n- 事项内容：{self.content}[{self.reminder_type.value}]\n- 触发时间：{self.date}\n- 重复规则：{self.recurrence.value}"


def normalize_date(date_str: str, daily: bool = False) -> str:
    """
    将各种日期字符串规范化为目标格式。
    daily=True -> 'HH:MM'
    daily=False -> 'YYYY-MM-DD HH:MM:SS'
    """
    dt = parser.parse(date_str)  # 自动解析多种格式

    if daily:
        return dt.strftime("%H:%M")
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class ScheduleTool(ToolBase):
    __tool_name__ = "schedule_reminder"
    __tool_description__ = "根据参数创建定时任务"
    __is_async__ = True
    plugin_function: Callable[..., str | None] | None = None

    @staticmethod
    async def a_tool_function(
        recurrence: Annotated[Recurrence, "重复规则"],
        content: Annotated[str, "任务内容的总结"],
        date: Annotated[str, "任务触发的时间。要结合当前时间分析任务真正的触发时间"],
        reminder_type: Annotated[ReminderType, "定时任务的类型"],
    ) -> str:
        try:
            if ScheduleTool.plugin_function is None:
                logger.warning("定时器暂时无法使用")
                return "定时器暂时无法使用"

            recurrence = Recurrence(recurrence)
            reminder_type = ReminderType(reminder_type)
            date = normalize_date(date, recurrence == Recurrence.DAILY)
            logger.info(
                f"调用{ScheduleTool.__tool_name__}: {recurrence} | {content} | {date} | {reminder_type}"
            )

            # 非正常时间，传递空数据
            if (recurrence == Recurrence.ONCE) and (
                datetime.strptime(date, "%Y-%m-%d %H:%M:%S") < datetime.now()
            ):
                return "不合法的时间！"

            data = ScheduleInfo(
                recurrence=recurrence,
                content=content,
                date=date,
                reminder_type=reminder_type,
            )
            await schedule_queue.put(data)
            return data.summary()
        except Exception as err:
            logger.error(f"Schedule Error: {err}")
            return "指定定时任务时出现了一个错误！"

    @staticmethod
    async def a_tool_post_processing_function(
        agent: AgentBase, agent_message: AgentMessage
    ) -> None:
        _ = agent
        agent_message.can_split = False

        # 空数据表示未触发任务
        if schedule_queue.empty() or ScheduleTool.plugin_function is None:
            return

        data: ScheduleInfo = await schedule_queue.get()
        # 设定group id，尝试建立提醒事项并调整message
        data.session_id = agent_message.session_id
        task_id: str | None = ScheduleTool.plugin_function(data=data)
        agent_message.content = (
            f"{agent_message.content}\n- 任务ID {task_id}"
            if task_id
            else "定时任务制定失败！"
        )

    @classmethod
    def get_tool(cls) -> Any:
        return FunctionTool.from_defaults(
            name=cls.__tool_name__,
            description=cls.__tool_description__,
            fn=cls.tool_function if not cls.__is_async__ else None,
            async_fn=cls.a_tool_function if cls.__is_async__ else None,
            return_direct=True,
        )
