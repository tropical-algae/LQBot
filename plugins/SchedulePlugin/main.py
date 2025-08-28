import uuid
from datetime import datetime

from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from lqbot import __version__ as __version__
from lqbot.core.agent.agent import agent
from lqbot.core.agent.tools.github_trend import (
    CodeLanguageType,
    PosterRankingPeriod,
    gen_trend_poster,
)
from lqbot.core.agent.tools.schedule import ReminderType, ScheduleInfo, ScheduleTool
from lqbot.core.agent.tools.schedule_remove import ScheduleRemoveTool
from lqbot.core.agent.tools.super_earth import hd_client
from lqbot.core.robot.handlers.sender import group_chat, send_group_message
from lqbot.utils.config import settings
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage, GroupMessageData, MessageType, QUserData

bot = CompatibleEnrollment


class SchedulePlugin(BasePlugin):
    name = "SchedulePlugin"  # 插件名
    version = __version__  # 插件版本

    @staticmethod
    def _gen_task_id() -> str:
        return f"TASK-{uuid.uuid4().hex.upper()[:8]}"

    async def on_load(self):
        # 注册到工具
        logger.info(f"{self.name}({self.version}) 插件已加载")
        ScheduleTool.plugin_function = self.register_scheduled
        ScheduleRemoveTool.plugin_function = self.remove_scheduled

        self.schedules: dict[str, ScheduleInfo] = {}
        self.job_map = {
            ReminderType.GITHUB_TREND: self.send_github_trend_poster,
            ReminderType.SUPER_EARTH_STATUS: self.send_super_earth_poster,
            ReminderType.MESSAGE: self.greet,
        }

    # ---------------- 服务注册与清除函数 ----------------#
    def register_scheduled(self, data: ScheduleInfo) -> str | None:
        # 必须提供group id
        if data.session_id is None:
            return None

        # 获取对应的服务function
        task_id = self._gen_task_id()
        job_func = self.job_map.get(data.reminder_type)
        if job_func is None:
            return None

        # 记录task id，添加日程表
        self.schedules[task_id] = data
        self.add_scheduled_task(
            job_func=job_func,
            name=task_id,
            interval=data.date,
            kwargs={"session_id": data.session_id, "content": data.content},
        )
        return task_id

    def remove_scheduled(self, task_id: str) -> ScheduleInfo | None:
        # task id 必须存在
        if task_id not in self.schedules:
            return None

        # 删除task id，删除日程表
        schedule_info = self.schedules.pop(task_id)
        self.remove_scheduled_task(task_id)
        return schedule_info

    # ---------------- 定时触发函数 ----------------#

    async def send_super_earth_poster(self, session_id: str, **kwargs) -> None:
        _ = kwargs

        news: str = await hd_client.get_dispatches()
        summary: AgentMessage = await agent.run(
            session_id=session_id,
            message=f"以下是一份从网页爬取的数据，请你对正文进行抽取并直接输出：\n{news}",
            use_agent=False,
        )
        await send_group_message(
            api=self.api,
            group_id=int(session_id),
            text=summary.content,
            text_type=MessageType.TEXT,
        )

    async def send_github_trend_poster(self, session_id: str, **kwargs) -> None:
        _ = kwargs

        url = f"{settings.GITHUB_TREND_API}/{PosterRankingPeriod.DAILY.value}/{CodeLanguageType.ALL.value}.json"
        filepath: str | None = await gen_trend_poster(url=url, session_id=session_id)
        await send_group_message(
            api=self.api,
            group_id=int(session_id),
            text=filepath,
            text_type=MessageType.IMAGE,
        )

    async def greet(self, content: str, session_id: str, **kwargs) -> None:
        _ = kwargs

        message = GroupMessageData(
            id=-1,
            content=f"这是用户要求你定时提醒他的事件/消息：'{content}'，请你润色一下这个消息，不用太正式",
            group_id=int(session_id),
            sender=QUserData(id=-1),
            from_bot=False,
            send_time=datetime.now(),
        )

        await group_chat(api=self.api, message=message, use_agent=False)
