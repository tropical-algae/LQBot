

import asyncio
from ncatbot.core import GroupMessage
from qq_bot.core.agent.base import AgentBase
from qq_bot.conn.sql.session import LocalSession
from qq_bot.conn.sql.crud.user_crud import select_user_by_name
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.util_text import trans_int
from qq_bot.utils.logging import logger


class ToolBase:
    tool_name: str
    description: dict
    
    @staticmethod
    def function(agent: AgentBase, user_msg: GroupMessageRecord, **kwargs) -> bool:
        pass
