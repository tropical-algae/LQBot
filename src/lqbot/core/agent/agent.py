import lqbot.core.agent.tools as agent_toolbox
from llama_index.core.agent.workflow import AgentOutput, FunctionAgent, ReActAgent
from llama_index.core.memory import (
    BaseMemoryBlock,
    FactExtractionMemoryBlock,
    InsertMethod,
    Memory,
    StaticMemoryBlock,
    VectorMemoryBlock,
)
from llama_index.core.workflow import Context
from llama_index.llms.openai import OpenAI
from lqbot.core.agent.tools.base import ToolBase
from lqbot.utils.config import settings
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage, MessageType
from lqbot.utils.util import import_all_modules_from_package


class Agent:
    def __init__(
        self,
        api_key: str,
        api_base: str,
        default_model: str,
        max_retries: int = 3,
        timeout: int = 30,
        system_prompt: str = "You are a helpful assistant",
        **kwargs,
    ):
        self.client = OpenAI(
            api_key=api_key,
            api_base=api_base,
            model=default_model,
            max_retries=max_retries,
            timeout=timeout,
            **kwargs,
        )
        self.blocks: list[BaseMemoryBlock] = [
            # 可选：常驻静态信息
            StaticMemoryBlock(
                name="profile",
                static_content="User prefers concise, Chinese responses.",
                priority=0,
            ),
            # 可选：事实抽取，自动从对话提炼结构化facts
            FactExtractionMemoryBlock(
                name="facts",
                llm=self.client,
                max_facts=200,
                priority=1,
            ),
        ]
        self.tools: dict[str, type[ToolBase]] = self.build_toolbox()
        self.context: dict[str, Context] = {}
        self.memories: dict[str, Memory] = {}
        self.agent = FunctionAgent(
            system_prompt=system_prompt,
            tools=[tool.get_tool() for tool in self.tools.values()],
            llm=self.client,
        )

    def _get_memory(self, session_id: str) -> Memory:
        return self.memories.setdefault(
            session_id,
            Memory.from_defaults(
                session_id=session_id,
                token_limit=1000,
                chat_history_token_ratio=0.7,
                token_flush_size=800,
                memory_blocks=self.blocks,
                insert_method=InsertMethod.USER,
            ),
        )

    def _get_context(self, session_id: str) -> Context:
        return self.context.setdefault(session_id, Context(self.agent))

    def build_toolbox(self) -> dict[str, type[ToolBase]]:
        import_all_modules_from_package(agent_toolbox)
        toolbox = ToolBase.__subclasses__()

        tools = {tool.__tool_name__: tool for tool in toolbox}
        logger.info(f"加载工具集: {list(tools.keys())}")
        return tools

    @staticmethod
    def build_default_agent_message(session_id: str, output: AgentOutput) -> AgentMessage:
        return AgentMessage(
            id=output.raw.get("id", "chatcmpl-NONEID"),  # type: ignore
            session_id=session_id,
            content=output.response.content,
            message_type=MessageType.TEXT,
            can_split=True,
        )

    async def run(self, session_id: str, message: str) -> AgentMessage:
        ctx = self._get_context(session_id)
        memory = self._get_memory(session_id)
        response: AgentOutput = await self.agent.run(
            user_msg=message, memory=memory, context=ctx
        )

        result = self.build_default_agent_message(session_id=session_id, output=response)
        for tool_call in response.tool_calls:
            tool = self.tools.get(tool_call.tool_name)
            if tool is None:
                continue
            tool.tool_post_processing_function(result)
            await tool.a_tool_post_processing_function(result)

        return result


agent = Agent(
    api_key=settings.API_KEY,
    api_base=settings.BASE_URL,
    default_model=settings.DEFAULT_MODEL,
    system_prompt=settings.SYSTEM_PROMPT,
)

# async def run():

#     while True:
#         user_msg = input("👤: ")
#         if user_msg.strip().lower() in {"exit", "quit"}:
#             break
#         resp = await agent.run(session_id="aaa", message=user_msg)
#         print("🤖:", resp.content)


# asyncio.run(run())
