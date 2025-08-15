import copy
import gzip
import json
import uuid

import aiofiles
from websockets.client import connect

from lqbot.utils.config import settings
from lqbot.utils.logger import logger

MESSAGE_TYPES = {
    11: "audio-only server response",
    12: "frontend server response",
    15: "error message from server",
}
MESSAGE_TYPE_SPECIFIC_FLAGS = {
    0: "no sequence number",
    1: "sequence number > 0",
    2: "last message from server (seq < 0)",
    3: "sequence number < 0",
}
MESSAGE_SERIALIZATION_METHODS = {0: "no serialization", 1: "JSON", 15: "custom type"}
MESSAGE_COMPRESSIONS = {0: "no compression", 1: "gzip", 15: "custom compression method"}

appid = settings.HUOSHAN_VOICE_LLM_APPID
token = settings.HUOSHAN_VOICE_LLM_TOKEN
cluster = settings.HUOSHAN_VOICE_LLM_CLUSTER
voice_type = "zh_female_wanwanxiaohe_moon_bigtts"
host = "openspeech.bytedance.com"
api_url = f"wss://{host}/api/v1/tts/ws_binary"

# version: b0001 (4 bits)
# header size: b0001 (4 bits)
# message type: b0001 (Full client request) (4bits)
# message type specific flags: b0000 (none) (4bits)
# message serialization method: b0001 (JSON) (4 bits)
# message compression: b0001 (gzip) (4bits)
# reserved data: 0x00 (1 byte)
default_header = bytearray(b"\x11\x10\x11\x00")

request_json: dict[str, dict] = {
    "app": {"appid": appid, "token": "access_token", "cluster": cluster},
    "user": {"uid": "388808087185088"},
    "audio": {
        "voice_type": "xxx",
        "encoding": "mp3",
        "speed_ratio": 1.0,
        "volume_ratio": 1.0,
        "pitch_ratio": 1.0,
    },
    "request": {"reqid": "xxx", "text": "xxx", "text_type": "plain", "operation": "xxx"},
}


async def voice_query(text: str, file: str = "test_query.mp3"):
    query_request_json: dict[str, dict] = copy.deepcopy(request_json)
    query_request_json["audio"]["voice_type"] = voice_type
    query_request_json["request"]["reqid"] = str(uuid.uuid4())
    query_request_json["request"]["operation"] = "query"
    query_request_json["request"]["text"] = text

    payload_bytes = str.encode(json.dumps(query_request_json))
    payload_bytes = gzip.compress(payload_bytes)  # if no compression, comment this line
    full_client_request = bytearray(default_header)
    full_client_request.extend(
        (len(payload_bytes)).to_bytes(4, "big")
    )  # payload size(4 bytes)
    full_client_request.extend(payload_bytes)  # payload
    logger.info("------------------------ test 'query' -------------------------")
    header = {"Authorization": f"Bearer; {token}"}
    async with (
        aiofiles.open(file, "wb") as file_to_save,
        connect(api_url, extra_headers=header, ping_interval=None) as ws,
    ):
        await ws.send(full_client_request)
        res = await ws.recv()
        await parse_response(res, file_to_save)


async def parse_response(res, file):
    logger.info("--------------------------- response ---------------------------")
    # logger.info(f"response raw bytes: {res}")
    protocol_version = res[0] >> 4
    header_size = res[0] & 0x0F
    message_type = res[1] >> 4
    message_type_specific_flags = res[1] & 0x0F
    serialization_method = res[2] >> 4
    message_compression = res[2] & 0x0F
    reserved = res[3]
    header_extensions = res[4 : header_size * 4]
    payload = res[header_size * 4 :]
    logger.info(
        f"            Protocol version: {protocol_version:#x} - version {protocol_version}"
    )
    logger.info(
        f"                 Header size: {header_size:#x} - {header_size * 4} bytes "
    )
    logger.info(
        f"                Message type: {message_type:#x} - {MESSAGE_TYPES[message_type]}"
    )
    logger.info(
        f" Message type specific flags: {message_type_specific_flags:#x} - {MESSAGE_TYPE_SPECIFIC_FLAGS[message_type_specific_flags]}"
    )
    logger.info(
        f"Message serialization method: {serialization_method:#x} - {MESSAGE_SERIALIZATION_METHODS[serialization_method]}"
    )
    logger.info(
        f"         Message compression: {message_compression:#x} - {MESSAGE_COMPRESSIONS[message_compression]}"
    )
    logger.info(f"                    Reserved: {reserved:#04x}")
    if header_size != 1:
        logger.info(f"           Header extensions: {header_extensions}")
    if message_type == 0xB:  # audio-only server response
        if message_type_specific_flags == 0:  # no sequence number as ACK
            logger.info("                Payload size: 0")
            return False
        sequence_number = int.from_bytes(payload[:4], "big", signed=True)
        payload_size = int.from_bytes(payload[4:8], "big", signed=False)
        payload = payload[8:]
        logger.info(f"             Sequence number: {sequence_number}")
        logger.info(f"                Payload size: {payload_size} bytes")
        await file.write(payload)
        return sequence_number < 0
    if message_type == 0xF:
        code = int.from_bytes(payload[:4], "big", signed=False)
        msg_size = int.from_bytes(payload[4:8], "big", signed=False)
        error_msg = payload[8:]
        if message_compression == 1:
            error_msg = gzip.decompress(error_msg)
        error_msg = str(error_msg, "utf-8")
        logger.info(f"          Error message code: {code}")
        logger.info(f"          Error message size: {msg_size} bytes")
        logger.info(f"               Error message: {error_msg}")
        return True
    if message_type == 0xC:
        msg_size = int.from_bytes(payload[:4], "big", signed=False)
        payload = payload[4:]
        if message_compression == 1:
            payload = gzip.decompress(payload)
        logger.info(f"            Frontend message: {payload}")
    logger.info("undefined message type!")
    return True


# if __name__ == '__main__':
#     loop = asyncio.get_event_loop()
#     # loop.run_until_complete(test_submit())
#     loop.run_until_complete(voice_query("你好啊，今天过的怎么样"))
