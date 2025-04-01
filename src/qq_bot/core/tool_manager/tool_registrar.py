
import json
from openai.types.chat import ChatCompletionMessageToolCall

from qq_bot.core.agent.base import AgentBase
from qq_bot.core.tool_manager.base import ToolRegistrarBase
from qq_bot.core.tool_manager.tools.base import ToolBase
from qq_bot.core.tool_manager.tools.timed_reminder_tool import TimedReminderTool
from qq_bot.core.llm_manager.llm_registrar import llm_registrar
from qq_bot.utils.models import GroupMessageRecord
from qq_bot.utils.logging import logger


class ToolRegistrar(ToolRegistrarBase):
    def __init__(self, agent: AgentBase):
        self.agent: AgentBase = agent
        self.tools: dict[str, ToolBase] = {TimedReminderTool.tool_name: TimedReminderTool}
        self.tool_dec: list[dict] = [TimedReminderTool.description]
    
    async def run(self, message: GroupMessageRecord) -> bool:
        results: list[ChatCompletionMessageToolCall] | None = await llm_registrar.get("bot_toolbox").run(message, tools=self.tool_dec)
        if results:
            for result in results:
                try:
                    func_name = result.function.name
                    func_args = json.loads(result.function.arguments)
                    tool = self.tools[func_name]
                    tool.function(self.agent, message, **func_args)
                except Exception as err:
                    logger.error(f"{err}. Tool [{func_name}] faild to run.")
            return True
        return False

