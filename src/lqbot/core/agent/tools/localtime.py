from datetime import datetime

from lqbot.core.agent.base import ToolBase
from lqbot.utils.logger import logger


class LocaltimeTool(ToolBase):
    __tool_name__ = "check_time"
    __tool_description__ = "检查当前时间"
    __is_async__ = False

    @staticmethod
    def tool_function() -> str:
        localtime = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {datetime.now().strftime('%A')}"
        logger.info(f"工具调用：检查当前时间 {localtime}")
        return localtime
