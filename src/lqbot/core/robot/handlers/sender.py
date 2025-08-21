import asyncio
import random

from ncatbot.core import BotAPI

from lqbot.core.agent.agent import agent
from lqbot.utils.config import settings
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage, GroupMessageData, MessageType, QUserData


async def send_group_message(
    api: BotAPI,
    group_id: int,
    text: str,
    text_type: MessageType = MessageType.TEXT,
    **kwargs,
) -> None:
    text_abs = text
    if text_type == MessageType.TEXT:
        text_abs = f"{text[:14]}..."
        await api.post_group_msg(group_id=group_id, text=text, **kwargs)
    elif text_type == MessageType.VOICE:
        await api.post_group_file(group_id=group_id, record=text, **kwargs)
    elif text_type == MessageType.IMAGE:
        await api.post_group_file(group_id=group_id, image=text, **kwargs)
    else:
        logger.info("消息发送失败：未知的数据类型")
        return
    logger.info(f"[GROUP {group_id}][机器人]: ({text_type.value}) {text_abs}")


async def group_chat(
    api: BotAPI, message: GroupMessageData, use_agent: bool = True, **kwargs
) -> bool:
    # agent / llm 推理
    group_id = message.group_id
    response: AgentMessage | None = await agent.run(
        str(group_id), message.content, use_agent, **kwargs
    )
    if not response:
        await send_group_message(api, group_id, "oops，好像出现了一点问题")
        return False

    # 分段发送文本
    async def send_content():
        contents: list[str] = (
            response.content_splited() if response.can_split else [response.content]
        )
        typing_times: list[float] = response.content_typing_times()

        for index, (content, typing_time) in enumerate(
            zip(contents, typing_times, strict=False)
        ):
            if index > 0:
                await asyncio.sleep(typing_time)
            await send_group_message(api, group_id, content)

    # 使用语音时，屏蔽文字
    voice_resp: bool = any(res.type == MessageType.VOICE for res in response.extras)
    if not voice_resp:
        await send_content()

    # 顺序发送附属资源
    for res in response.extras:
        res_content: str | None = await res.get_content()
        res_type = res.type
        if not res_content:
            res_content = f"[{res.type.value}] 资源获取失败"
            res_type = MessageType.TEXT
        await send_group_message(api, group_id, res_content, text_type=res_type)

    return True
