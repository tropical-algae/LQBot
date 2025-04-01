import json
import os
import random
from typing import Generator
import requests

from qq_bot.utils.config import settings


class RandomPicLoader:
    def __init__(
        self, 
        cache_root: str, 
        api_v1: str,
        api_v2: str
    ):
        self.cache_root = cache_root
        self.api_v1 = api_v1
        self.api_v2 = api_v2
        os.makedirs(cache_root, exist_ok=True)
    
    def load(self) -> tuple[str | None, str | None]:
        sort = random.choices(["setu", "ws", "r18"], weights=[0.6, 0.4], k=1)[0]
        response = requests.post(self.api_v1, params={"sort": sort})
        if response.status_code == 200:
            url = response.url
            pic_response = requests.get(url)

            # 确保请求成功
            if pic_response.status_code == 200:
                file_path = os.path.join(self.cache_root, url.split("/")[-1])
                with open(file_path, 'wb') as f:
                    f.write(pic_response.content)
                return file_path, url
        return None, None
    
    def load_r18(self, num: int = 1) -> Generator[tuple[str | None, str | None], None, None]:
        response = requests.post(self.api_v2, params={"r18": 1, "num": num})
        if response.status_code == 200:
            urls = [r["url"] for r in json.loads(response.text)]
            
            for url in urls:
                pic_response = requests.get(url)

                # 确保请求成功
                if pic_response.status_code == 200:
                    file_path = os.path.join(self.cache_root, url.split("/")[-1])
                    with open(file_path, 'wb') as f:
                        f.write(pic_response.content)
                    yield file_path, url
    

random_pic = RandomPicLoader(
    cache_root=settings.RANDOM_PIC_CACHE_ROOT,
    api_v1=settings.RANDOM_PIC_API_v1,
    api_v2=settings.RANDOM_PIC_API_v2,
)


