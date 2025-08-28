import uuid

from llama_index.core.agent.workflow import AgentOutput, FunctionAgent, ReActAgent
from llama_index.core.llms import CompletionResponse
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

import lqbot.core.agent.tools as agent_toolbox
from lqbot.core.agent.base import AgentBase, ToolBase
from lqbot.utils.config import settings
from lqbot.utils.decorator import exception_handling
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage, MessageType
from lqbot.utils.util import import_all_modules_from_package


class LQAgent(AgentBase):
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
        self.tools: dict[str, type[ToolBase]] = {}
        self.context: dict[str, Context] = {}
        self.memories: dict[str, Memory] = {}
        # 工具注册
        self._load_tools()

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
                token_limit=1200,
                chat_history_token_ratio=0.7,
                token_flush_size=800,
                memory_blocks=self.blocks,
                insert_method=InsertMethod.USER,
            ),
        )

    def _get_context(self, session_id: str) -> Context:
        return self.context.setdefault(session_id, Context(self.agent))

    def _load_tools(self) -> None:
        # 自动加载全部工具
        import_all_modules_from_package(agent_toolbox)
        toolbox = ToolBase.__subclasses__()

        tools: dict[str, type[ToolBase]] = {}
        unactivated_tools: list[str] = []
        # 统计可用工具
        for tool in toolbox:
            if tool.__activate__:
                tools[tool.__tool_name__] = tool
            else:
                unactivated_tools.append(tool.__tool_name__)

        self.tools = tools
        logger.info(f"已加载工具: {list(self.tools.keys())}")
        logger.info(f"未加载的工具: {unactivated_tools}")

    @staticmethod
    def _build_agent_message(
        session_id: str, output: AgentOutput | CompletionResponse
    ) -> AgentMessage:
        try:
            id = (
                output.raw.get("id", f"chatcmpl-{uuid.uuid4().hex}")  # type: ignore
                if isinstance(output, AgentOutput)
                else output.raw.id  # type: ignore
            )
        except Exception:
            id = f"chatcmpl-{uuid.uuid4().hex}"
        content = (
            output.response.content if isinstance(output, AgentOutput) else output.text
        )

        return AgentMessage(
            id=id,
            session_id=session_id,
            content=content,
            can_split=True,
        )

    async def _run_llm(self, session_id: str, message: str, **kwargs) -> AgentMessage:
        # 大模型直接推理
        response = await self.client.acomplete(prompt=message, **kwargs)
        result = self._build_agent_message(session_id=session_id, output=response)
        return result

    async def _run_agent(self, session_id: str, message: str, **kwargs) -> AgentMessage:
        # 获取记忆，agent推理
        ctx = self._get_context(session_id)
        memory = self._get_memory(session_id)
        response: AgentOutput = await self.agent.run(
            user_msg=message, memory=memory, context=ctx, **kwargs
        )
        # 封装结果
        result = self._build_agent_message(session_id=session_id, output=response)
        # 封装结果后处理
        for tool_call in response.tool_calls:
            tool = self.tools.get(tool_call.tool_name)
            if tool is None:
                continue
            try:
                tool.tool_post_processing_function(self, result)
                await tool.a_tool_post_processing_function(self, result)
            except Exception as err:
                logger.error(f"工具 {tool.__tool_name__} 后处理方法运行失败：{err}")

        return result

    async def reset_memory(self, session_id: str) -> None:
        memory: Memory | None = self.memories.get(session_id)
        if memory:
            await memory.areset()

    @exception_handling
    async def run(
        self, session_id: str, message: str, use_agent: bool = True, **kwargs
    ) -> AgentMessage | None:
        return (
            await self._run_agent(session_id=session_id, message=message, **kwargs)
            if use_agent
            else await self._run_llm(session_id=session_id, message=message, **kwargs)
        )


agent = LQAgent(
    api_key=settings.API_KEY,
    api_base=settings.BASE_URL,
    default_model=settings.DEFAULT_MODEL,
    system_prompt=settings.AGENT_PROMPT,
)
