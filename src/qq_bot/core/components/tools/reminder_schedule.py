import asyncio

from sqlmodel import Session
from qq_bot.core.robot.base import AgentBase
from qq_bot.core.components.tools.base import ToolBase
from qq_bot.utils.decorator import sql_session, tools_logger
from qq_bot.utils.models import GroupMessageData
from qq_bot.utils.logger import logger


@tools_logger
class ReminderScheduleTool(ToolBase):
    tool_name = "reminder_schedule"
    description = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": "定时提醒某人要做某事（必须包含被提醒人、时间、提醒事项三个要素）",
            "parameters": {
                "type": "object",
                "required": ["user", "time", "message"],
                "properties": {
                    "user": {
                        "type": "string",
                        "description": "你要提醒的那位用户的昵称",
                    },
                    "time": {
                        "type": "string",
                        "description": "何时提醒（注意分析时间），遵循格式：YYYY-MM-DD HH:MM:SS",
                    },
                    "message": {
                        "type": "string",
                        "description": "（以第一人称角度）完整的事项描述",
                    },
                },
            },
        },
        "is_meta": False,
    }

    @staticmethod
    def function(
        agent: AgentBase,
        user_msg: GroupMessageData,
        user: str,
        time: str,
        message: str,
    ) -> bool:
        def send_message_to_user_wrapper():
            @sql_session
            async def send_message_to_user(db: Session):
                # 查找用户ID
                # umodel = select_user_by_name(db=db, name=user)
                # uid = trans_int(umodel.id) if umodel else None

                uid: int | None = None
                response = await agent.api.get_group_member_list(user_msg.group_id)
                if response["status"] == "ok":
                    uid = next(
                        (
                            umodel["user_id"]
                            for umodel in response["data"]
                            if umodel["nickname"] == user
                        ),
                        None,
                    )

                text = f"{message}\n"
                if uid is None:
                    text = f"TO: {user}\n{message}"

                # 发送消息
                result = await agent.api.post_group_msg(
                    group_id=user_msg.group_id, at=uid, text=text
                )
                if result["status"] == "ok":
                    logger.info(f"定时提醒已触发: [主体 - {user}]{time} -> {message}")
                else:
                    logger.error(f"定时提醒发送失败: [主体 - {user}]{time} -> {message}")

            asyncio.get_event_loop().create_task(send_message_to_user())
            # asyncio.create_task(send_message_to_user())

        try:
            # 添加定时任务
            agent.add_scheduled_task(
                job_func=send_message_to_user_wrapper,
                name="定时提醒",
                interval=time,
                # kwargs=
            )

            # 发送提示信息
            asyncio.get_event_loop().create_task(
                agent.api.post_group_msg(
                    group_id=user_msg.group_id,
                    text=f"已建立日程提醒任务\n主体人: {user}\nTime: {time}\nTheme: {user_msg.content}\n",
                    at=user_msg.sender.id,
                )
            )

            return True
        except Exception as err:
            logger.error(err)
            return False
