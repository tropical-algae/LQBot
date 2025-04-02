from qq_bot.core.agent.base import AgentBase
from qq_bot.utils.models import GroupMessageRecord


class ToolBase:
    tool_name: str
    description: dict

    @staticmethod
    def function(agent: AgentBase, user_msg: GroupMessageRecord, **kwargs) -> bool:
        pass
