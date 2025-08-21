# ruff: noqa: N815
import asyncio
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated

import httpx
import imgkit
import markdown
from pydantic import BaseModel

from lqbot.core.agent.base import AgentBase, InformationBase, ToolBase
from lqbot.utils.config import settings
from lqbot.utils.decorator import exception_handling
from lqbot.utils.logger import logger
from lqbot.utils.models import AgentMessage, AgentResource, MessageType

# 固定路径 不需写配置文件
IMGKIT_CSS = "asset/other/imgkit.css"
IMGKIT_CACHE_ROOT = Path(settings.CACHE_ROOT) / "github_trend"
IMGKIT_CACHE_ROOT.mkdir(parents=True, exist_ok=True)
IMGKIT_OPTIONS = {
    "format": "png",
    "encoding": "UTF-8",
    "quality": 100,
    "width": 800,
    "enable-local-file-access": None,
}

url_queue: asyncio.Queue = asyncio.Queue()


def md_link(url: str) -> str:
    return f"""<span style="color: #1382BE;">`{url}`</span>"""


class CodeLanguageType(str, Enum):
    CPP = "cpp"
    C = "c"
    GO = "go"
    PYTHON = "python"
    RUST = "rust"
    HTML = "html"
    JAVA = "java"
    R = "r"
    JAVASCRIPT = "javascript"
    CSHARP = "c#"
    RUBY = "ruby"
    ALL = "all"


class RankingPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class Contributor(InformationBase):
    avatar: str
    name: str
    url: str

    def summary(self, **kwargs) -> str:
        show_avatar = kwargs.get("show_avatar", False)
        return (
            f"![]({self.avatar})"
            if show_avatar
            else f"- {self.name} ( {md_link(self.url)} )"
        )


class GithubRepoItem(InformationBase):
    title: str
    url: str
    description: str
    language: str
    languageColor: str
    stars: str
    forks: str
    addStars: str
    contributors: list[Contributor]

    def summary(self, **kwargs) -> str:
        show_avatar = kwargs.get("show_avatar", False)
        contributors = "\n".join(
            contrb.summary(show_avatar=show_avatar) for contrb in self.contributors
        )
        return f"""## Repository: {self.title} <span style="color: {self.languageColor};">({self.language})</span>

**STARS**: `{self.stars}` | **FORKS**: `{self.forks}` | **ADDED STARS**: `{self.addStars}` | **URL**: {md_link(self.url)}

{self.description}

**Contributors**:

{contributors}"""


class GithubTrend(InformationBase):
    title: str
    description: str
    link: str
    pubDate: str
    items: list[GithubRepoItem]

    def summary(self, **kwargs) -> str:
        show_avatar = kwargs.get("show_avatar", False)
        title = f"""# {self.title}

{self.description}

DATE: {self.pubDate}

LINK: {md_link(self.link)}

---

"""

        content = """
<hr style="border: none; height: 0; background: transparent;">
""".join(item.summary(show_avatar=show_avatar) for item in self.items)
        return title + content


async def get_trend_info(url: str) -> GithubTrend | None:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            return GithubTrend.model_validate(data)
    except Exception as err:
        logger.error(f"Github Trend summary error: {err}")
        return None


@exception_handling
async def gen_trend_poster(url: str, session_id: str | None = None) -> str | None:
    type_name: str = MessageType.IMAGE.value
    trend: GithubTrend | None = await get_trend_info(url)
    date = datetime.date(datetime.now()).isoformat()
    filepath = IMGKIT_CACHE_ROOT / f"{type_name}-{date}-{uuid.uuid4().hex[:8]}.png"
    if trend:
        trend_md = trend.summary(show_avatar=True)
        trend_html = markdown.markdown(trend_md)
        imgkit.from_string(trend_html, filepath, options=IMGKIT_OPTIONS, css=IMGKIT_CSS)
        logger.info(f"[GROUP {session_id or 'Unknown'}] 生成 {type_name} {filepath}")
        return str(filepath)
    logger.error(f"[GROUP {session_id or 'Unknown'}] {type_name} {filepath} 生成失败")
    return None


class GithubTrendTool(ToolBase):
    __tool_name__ = "check_github_trend"
    __tool_description__ = "获取github趋势信息"
    __is_async__ = True

    @staticmethod
    @exception_handling(default_return="github趋势参数分析失败")
    async def a_tool_function(
        language_type: Annotated[CodeLanguageType, "编程语言类型。若未指定则默认是all"],
        period: Annotated[RankingPeriod, "趋势的统计周期。若未指定则默认是daily"],
    ) -> str:
        language_type = CodeLanguageType(language_type)
        period = RankingPeriod(period)
        url = f"{settings.GITHUB_TREND_API}/{period.value}/{language_type.value}.json"
        await url_queue.put(url)

        return "正在收集Github趋势"

    @staticmethod
    async def a_tool_post_processing_function(
        agent: AgentBase, agent_message: AgentMessage
    ) -> None:
        _ = agent
        url: str = await url_queue.get()
        agent_message.extras.append(
            AgentResource(
                type=MessageType.IMAGE,
                func=gen_trend_poster,
                params={"url": url, "session_id": agent_message.session_id},
            )
        )
