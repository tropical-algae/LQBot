from lqbot.core.agent.tools.base import ToolBase
from lqbot.utils.models import AgentMessage, MessageType


class VoiceRequestTool(ToolBase):
    __tool_name__ = "voice_request_tool"
    __tool_description__ = (
        "若用户要求使用语音回复，请调用。调用时请正常回复用户，不需要特别声明使用了工具"
    )
    __is_async__ = False

    @staticmethod
    def tool_function() -> str:
        return "ok"

    @staticmethod
    def tool_post_processing_function(agent_message: AgentMessage) -> None:
        agent_message.can_split = False
        agent_message.message_type = MessageType.VOICE
