import asyncio
from pathlib import Path
import random
import uuid
from ncatbot.core import GroupMessage, BotAPI

from qq_bot.core.agent.agent import agent
from qq_bot.core.robot.handlers.voice import voice_query
from qq_bot.utils.models import AgentMessage, GroupMessageData, MessageType, QUserData

from qq_bot.utils.config import settings
from qq_bot.utils.logger import logger


TTS_ROOT = Path(settings.CACHE_ROOT) / "tts"
TTS_ROOT.mkdir(parents=True, exist_ok=True)


async def send_group_message(
    api: BotAPI, group_id: int, text: str, voice: bool = True, **kwargs
) -> GroupMessageData | None:
    text_abs = f"{text[:7]}..."
    
    if voice:
        file_name = f"voice_{uuid.uuid4().hex}.mp3"
        filepath = TTS_ROOT / file_name
        
        
        await voice_query(file=str(filepath), text=text)
        
        if filepath.exists():
            await api.post_group_file(group_id=group_id, record=str(f"/cache/tts/{file_name}"))
            logger.info(f"[GROUP {group_id}][bot]:\t<语音 {filepath}> {text_abs}")
    else:
        await api.post_group_msg(group_id=group_id, text=text, **kwargs)
        logger.info(f"[GROUP {group_id}][bot]:\t{text_abs}")


async def group_chat(
    api: BotAPI,
    message: GroupMessageData,
) -> bool:
    group_id = message.group_id
    
    response: AgentMessage = await agent.run(session_id=str(group_id), message=message.content)
    
    if not response:
        return False
    
    voice_response: bool = response.message_type == MessageType.VOICE
    contents: list[str] = response.content_splited() if response.can_split else [response.content]
    typing_times: list[float] = response.content_typing_times()
    
    for index, (content, typing_time) in enumerate(zip(contents, typing_times)):
        if (index > 0) and (response.message_type == MessageType.TEXT):
            await asyncio.sleep(typing_time)
        await send_group_message(api, group_id, content, voice=voice_response)

    return True
