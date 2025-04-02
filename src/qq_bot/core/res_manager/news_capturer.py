import json
import random
import requests

from qq_bot.utils.decorator import function_retry
from qq_bot.utils.logging import logger
from qq_bot.utils.config import settings


class NewsLoader:
    def __init__(self, url: str, sources: list[str]) -> tuple[str, list] | None:
        self.url = f"{url}{'' if url.endswith('/') else '/'}"
        self.sources: list[str] = sources

    @function_retry(times=3)
    def get_news(self, source: str | None = None, max_len: int = 10) -> dict:
        if (not source) or (source not in self.sources):
            source = random.choice(self.sources)
        url = f"{self.url}{source}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = json.loads(response.text)
                if data["code"] == 200:
                    source_name = data["message"]
                    source_news = data["obj"][:max_len]
                    logger.info(
                        f"收集实时热搜 -> 信源[{source_name}] 数量：{len(source_news)}"
                    )
                    return (source_name, source_news)
                logger.error(f"{source}热搜收集失败 -> 目标站点访问失败")

            logger.error(f"{source}热搜收集失败 -> 信源API访问失败")

        except Exception as err:
            logger.error(f"收集热搜时发生一个错误: {err}")
            return None
        return None


news_loader = NewsLoader(url=settings.NEWS_API, sources=settings.NEWS_SOURCES)
