from lqbot.core.agent.base import AgentBase, ToolBase
from lqbot.utils.models import AgentMessage, MessageType


class VoiceRequestTool(ToolBase):
    __tool_name__ = "voice_request_tool"
    __tool_description__ = (
        "工具作用：使用文本生成语音\n"
        "触发方式：当用户要求使用语音回复时调用\n"
        "要求：调用时请正常与用户聊天，不要特别声明你使用了该语音生成工具\n"
    )
    __is_async__ = False

    @staticmethod
    def tool_function() -> str:
        return "ok"

    @staticmethod
    def tool_post_processing_function(
        agent: AgentBase, agent_message: AgentMessage
    ) -> None:
        _ = agent
        agent_message.can_split = False
        agent_message.message_type = MessageType.VOICE
