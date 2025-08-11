from qq_bot.core.robot.base import AgentBase
from qq_bot.utils.models import GroupMessageData


class ToolBase:
    tool_name: str
    description: dict

    @staticmethod
    def function(agent: AgentBase, user_msg: GroupMessageData, **kwargs) -> bool:
        pass
