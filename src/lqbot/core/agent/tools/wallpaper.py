import json
import os
import random
from collections.abc import Generator
from pathlib import Path

import requests  # type: ignore

from lqbot.base import ComponentBase
from lqbot.utils.config import settings
from lqbot.utils.decorator import require_active


class WallpaperProvider(ComponentBase):
    __component_name__ = settings.WALLPAPER_COMPONENT_NAME

    def __init__(self, cache_root: str | Path, api_v1: str, api_v2: str):
        super().__init__(cache_root=cache_root, api_v1=api_v1, api_v2=api_v2)
        self.cache_root: Path = Path(cache_root)
        self.api_v1 = api_v1
        self.api_v2 = api_v2
        self.cache_root.mkdir(parents=True, exist_ok=True)

    @require_active
    def load(self) -> tuple[str | None, str | None]:
        sort = random.choices(["setu", "ws"], weights=[0.6, 0.4], k=1)[0]
        response = requests.post(self.api_v1, params={"sort": sort})
        if response.status_code == 200:
            url = response.url
            pic_response = requests.get(url)

            # 确保请求成功
            if pic_response.status_code == 200:
                file_path = self.cache_root / url.split("/")[-1]
                with open(file_path, "wb") as f:
                    f.write(pic_response.content)
                return str(file_path), url
        return None, None

    @require_active
    def load_r18(
        self, num: int = 1
    ) -> Generator[tuple[str | None, str | None], None, None]:
        response = requests.post(self.api_v2, params={"r18": 1, "num": num})
        if response.status_code == 200:
            urls = [r["url"] for r in json.loads(response.text)]

            for url in urls:
                pic_response = requests.get(url)

                # 确保请求成功
                if pic_response.status_code == 200:
                    file_path = self.cache_root / url.split("/")[-1]
                    with open(file_path, "wb") as f:
                        f.write(pic_response.content)
                    yield str(file_path), url


wallpaper_provider = WallpaperProvider(
    cache_root=Path(settings.CACHE_ROOT) / "wallpaper",
    api_v1=settings.WALLPAPER_API,
    api_v2=settings.WALLPAPER_R18_API,
)

# for local_file_origin, url in wallpaper_provider.load_r18(num=2):
#     print(local_file_origin + "  " + url)
