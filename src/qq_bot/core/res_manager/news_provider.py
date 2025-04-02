import json
import random
import requests

from qq_bot.utils.decorator import function_retry
from qq_bot.utils.logging import logger
from qq_bot.utils.config import settings


class NewsProvider:
    def __init__(self, url: str, sources: dict[str, str]) -> tuple[str, list] | None:
        self.url = f"{url}{'' if url.endswith('/') else '/'}"
        self.sources: dict[str, str] = sources
        self.sources_name: list[str] = list(sources.keys())

    @function_retry(times=3)
    def get_news(self, source_name: str | None = None, max_len: int = 8) -> dict:
        # 未注明信源、或是无效信源时，随机抽
        if (not source_name) or (source_name not in self.sources_name):
            source_name = random.choice(self.sources_name)
        source = self.sources[source_name]
        url = f"{self.url}{source}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = json.loads(response.text)
                if data["code"] == 200:
                    # source_name = data["message"]
                    source_news = data["obj"][:max_len]
                    logger.info(
                        f"收集实时热搜 -> 信源[{source_name}] 数量：{len(source_news)}"
                    )
                    return (source_name, source_news)
                logger.error(f"[{source_name}]热搜收集失败 -> 目标站点访问失败")
                return None

            logger.error(f"[{source_name}]热搜收集失败 -> 信源API访问失败")

        except Exception as err:
            logger.error(f"收集[{source_name}]热搜时发生一个错误: {err}")
        return None


news_provider = NewsProvider(url=settings.NEWS_API, sources=settings.NEWS_SOURCES)
