import os
import jmcomic
from qq_bot.utils.config import settings
from qq_bot.utils.logging import logger


class JMProvider:
    def __init__(self, cache_root: str, option_path: str) -> list:
        self.cache_root = cache_root
        self.option = jmcomic.create_option_by_file(option_path)
        os.makedirs(cache_root, exist_ok=True)

    def download(self, id: int) -> list:
        if str(id) not in os.listdir(self.cache_root):
            logger.info(f"Downloading jm [{id}] file...")
            jmcomic.download_album(id, option=self.option)

        file_root = os.path.join(self.cache_root, str(id))
        if os.path.isdir(file_root):
            sub_dirs = sorted(
                [i for i in os.listdir(file_root)],
                key=lambda x: int(x.split(".")[0]),
                reverse=False,
            )
            chapter_roots = [
                os.path.join(file_root, i)
                for i in sub_dirs
                if os.path.isdir(os.path.join(file_root, i))
            ]
            return chapter_roots
        return []


jm_provider = JMProvider(
    cache_root=settings.JM_CACHE_ROOT, option_path=settings.JM_OPTION
)
