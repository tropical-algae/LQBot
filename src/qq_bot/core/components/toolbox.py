import json
from openai.types.chat import ChatCompletionMessageToolCall

from qq_bot.core.robot.base import AgentBase
from qq_bot.base import ComponentBase
from qq_bot.core.components.tools.base import ToolBase
from qq_bot.core import llm_registrar
from qq_bot.utils.decorator import require_active
from qq_bot.utils.models import GroupMessageData
from qq_bot.utils.logger import logger
from qq_bot.utils.util import import_all_modules_from_package
import qq_bot.core.components.tools as bot_tools
from qq_bot.utils.config import settings


class ToolRegistrar(ComponentBase):
    __component_name__ = settings.TOOLBOX_COMPONENT_NAME
    
    def __init__(self):
        super().__init__()
        self._load_tools()

    def _load_tools(self):
        import_all_modules_from_package(bot_tools)

        tools = ToolBase.__subclasses__()
        logger.info("正在注册Agent工具")

        self.tools: dict[str, ToolBase] = {tool.tool_name: tool for tool in tools}
        self.tool_dec: list[dict] = [tool.description for tool in tools]

        logger.info(f"已注册Agent工具: {', '.join(self.tools.keys())}")

    @require_active
    async def run(self, agent: AgentBase, message: GroupMessageData) -> bool:
        results: list[ChatCompletionMessageToolCall] | None = await llm_registrar.get(
            "bot_toolbox"
        ).run(message, tools=self.tool_dec)
        if results:
            for result in results:
                try:
                    func_name = result.function.name
                    func_args = json.loads(result.function.arguments)
                    tool = self.tools[func_name]
                    tool.function(agent, message, **func_args)
                except Exception as err:
                    logger.error(f"{err}. 工具 [{func_name}] 调用失败")
            return True
        return False

tool_component = ToolRegistrar()
