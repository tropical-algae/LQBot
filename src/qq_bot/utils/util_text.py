import json
import random
import re
import string
from typing import Literal
from qq_bot.utils.logger import logger


def get_data_from_message(message: list[dict], type: str) -> dict:
    return next((item["data"] for item in message if item.get("type") == type), {})


def extract_json_from_markdown(text: str) -> list[dict | list]:
    results = []
    pattern = r"```json\s*([\s\S]*?)\s*```"
    matches = re.findall(pattern, text)
    for index, match in enumerate(matches):
        try:
            parsed = json.loads(match)
            results.append(parsed)
        except Exception as err:
            logger.warning(f"文本段中第{index + 1}个JSON解析失败! 文本: {text}")
            continue
    return results


def parse_text(text):
    lines = text.split("\n")
    count = 0
    for i, line in enumerate(lines):
        if "```" in line:
            count += 1
            items = line.split("`")
            if count % 2 == 1:
                lines[i] = f'<pre><code class="{items[-1]}">'
            else:
                lines[i] = f"</code></pre>"
        else:
            if i > 0:
                if count % 2 == 1:
                    line = line.replace("&", "&amp;")
                    line = line.replace('"', "&quot;")
                    line = line.replace("'", "&apos;")
                    line = line.replace("<", "&lt;")
                    line = line.replace(">", "&gt;")
                    line = line.replace(" ", "&nbsp;")
                lines[i] = "<br/>" + line
    return "".join(lines)


def language_classifity(sentence: str) -> Literal["zh", "en"]:
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", sentence)
    english_chars = re.findall(r"[a-zA-Z]", sentence)

    if len(chinese_chars) > len(english_chars):
        return "zh"
    elif len(english_chars) > len(chinese_chars):
        return "en"


def strip_trailing_punct(line: str, lang: str) -> str:
    line = line.strip()
    if lang == "zh":
        return re.sub(r"[。！？~～]+$", "", line)
    else:  # English
        return line.rstrip(string.punctuation)


def split_sentence_zh(text: str, strip_punct: bool) -> list[str]:
    text = text.strip()
    text = re.sub(r"([。！？~～?.])([^”’])", r"\1\n\2", text)
    text = re.sub(r"([\.。]{2,}|…{2,})([^”’])", r"\1\n\2", text)
    text = re.sub(r"([。！？~～?.][”’])([^，。！？?.])", r"\1\n\2", text)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return [strip_trailing_punct(line, "zh") if strip_punct else line for line in lines]


def split_sentence_en(text: str, strip_punct: bool) -> list[str]:
    text = text.strip()
    text = re.sub(r"([.!?])(\s+)([A-Z])", r"\1\n\3", text)
    text = text.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return [strip_trailing_punct(line, "en") if strip_punct else line for line in lines]


def auto_split_sentence(
    text: str, language: Literal["zh", "en", None] = None, strip_punct: bool = True
) -> list[str]:
    language = language if language else language_classifity(text)
    if language == "zh":
        return split_sentence_zh(text, strip_punct)
    else:
        return split_sentence_en(text, strip_punct)


def typing_time_calculate(text: str, language: Literal["zh", "en", None] = None) -> float:
    language = language if language else language_classifity(text)
    typing_time = len(text) / 3.0 / (5.0 if language == "en" else 1.0)
    return typing_time + random.random()


def trans_int(data: int | str | None) -> int | None:
    return int(data) if data else None


def trans_str(data: int | str | None) -> str | None:
    return str(data) if data else None
