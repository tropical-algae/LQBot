import re
import json
import yaml
import random
import string
import pkgutil
import importlib
from PIL import Image
from typing import Literal
from qq_bot.utils.logger import logger


def load_yaml(yaml_path: str) -> dict:
    try:
        with open(yaml_path) as yaml_file:
            return yaml.safe_load(yaml_file)
    except Exception as err:
        logger.error(
            f"[YAML Reader] Error occured when read YAML from path '{yaml_path}'. Error: {err}"
        )
        return {}


def import_all_modules_from_package(package):
    """自动导入指定包中的所有模块

    Args:
        package (_type_): 包名
    """
    for _, modname, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        importlib.import_module(modname)


def stitched_images(images: list[Image.Image]) -> Image.Image | None:
    if len(images) > 0:
        width = 1024

        new_images = []
        for image in images:
            w, h = image.size
            new_images.append(image.resize((width, int(h * width / w)), Image.LANCZOS))

        # width, _ = images[0].size
        mode = new_images[0].mode
        height = sum(i.size[1] for i in new_images)

        result = Image.new(mode=mode, size=(width, height))

        current_height = 0
        for i, image in enumerate(new_images):
            result.paste(image, box=(0, current_height))
            current_height += image.size[1]
        return result


def blue_image(image: Image.Image) -> Image.Image:
    from PIL import ImageFilter

    return image.filter(ImageFilter.BLUR)


def get_data_from_message(message: list[dict], type: str) -> dict:
    return next((item["data"] for item in message if item.get("type") == type), {})


def text_simplification(text: str, max_len: int = 250) -> str:
    text = re.sub(r' {2,}', ' ', text)
    text = text[-max_len:]
    return text


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
