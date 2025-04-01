from qq_bot.core.agent.agent_server import send_msg_2_group
from qq_bot.core.agent.base import AgentBase
from qq_bot.utils.decorator import tools_logger
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.logging import logger

@tools_logger
class DataUpdateTool:
    tool_name = "data_update"
    description = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": "更新用户数据（当用户明确要求更新用户信息时触发）",
            "parameters": {
                "type": "object",
                "required": ["user"],
                "properties": {
                    "user": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "单个用户名。如果为 'ALL'，表示更新所有用户信息。"
                        },
                        "description": "要被更新的用户名列表，或仅包含一个 'ALL' 表示更新全员。"
                    },
                },
            },
            "is_meta": False
        }
    }

    @staticmethod
    def function(
        agent: AgentBase,
        user_msg: GroupMessageRecord,
        user: list[str]
    ) -> bool:
        try:
            # 发送提示信息
            send_msg_2_group(
                api=agent.api,
                group_id=user_msg.group_id, 
                text="",
                at=user_msg.sender.id
            )
            return True
        except Exception as err:
            logger.error(err)
            return False
