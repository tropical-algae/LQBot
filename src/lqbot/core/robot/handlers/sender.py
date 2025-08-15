import asyncio
import random
import uuid
from pathlib import Path

from ncatbot.core import BotAPI, GroupMessage

from lqbot.core.agent.agent import agent
from lqbot.core.robot.handlers.voice import voice_query
from lqbot.utils.config import settings
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage, GroupMessageData, MessageType, QUserData

TTS_ROOT = Path(settings.CACHE_ROOT) / "tts"
TTS_ROOT.mkdir(parents=True, exist_ok=True)


async def send_group_message(
    api: BotAPI, group_id: int, text: str, voice: bool = True, **kwargs
) -> None:
    text_abs = f"{text[:7]}..."

    if voice:
        file_name = f"voice_{uuid.uuid4().hex}.mp3"
        filepath = TTS_ROOT / file_name

        await voice_query(file=str(filepath), text=text)

        if filepath.exists():
            await api.post_group_file(
                group_id=group_id, record=str(f"/cache/tts/{file_name}")
            )
            logger.info(f"[GROUP {group_id}][bot]:\t<语音 {filepath}> {text_abs}")
            return
        await api.post_group_msg(group_id=group_id, text=text, **kwargs)
        logger.info(f"[GROUP {group_id}][bot]:\t{text_abs}")


async def group_chat(
    api: BotAPI,
    message: GroupMessageData,
) -> bool:
    group_id = message.group_id

    response: AgentMessage = await agent.run(
        session_id=str(group_id), message=message.content
    )

    if not response:
        return False

    voice_response: bool = response.message_type == MessageType.VOICE
    contents: list[str] = (
        response.content_splited() if response.can_split else [response.content]
    )
    typing_times: list[float] = response.content_typing_times()

    for index, (content, typing_time) in enumerate(
        zip(contents, typing_times, strict=False)
    ):
        if (index > 0) and (response.message_type == MessageType.TEXT):
            await asyncio.sleep(typing_time)
        await send_group_message(api, group_id, content, voice=voice_response)

    return True
