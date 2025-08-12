import os
from pathlib import Path
from qq_bot.utils.config import settings
from qq_bot.utils.logger import logger
from qq_bot.core.llm.base import OpenAIBase
import qq_bot.core.llm.llms as bot_llms
from qq_bot.utils.util import import_all_modules_from_package


class LLMRegistrar:
    def __init__(self, prompt_root: str | Path):
        self.prompt_root: Path = Path(prompt_root)
        self.model_services: dict[str, OpenAIBase] = {}
        
        self.prompt_root.mkdir(parents=True, exist_ok=True)
        self._load_model_services()

    def _load_model_services(self) -> None:
        import_all_modules_from_package(bot_llms)

        model_services = OpenAIBase.__subclasses__()
        logger.info("正在注册模型服务")
        for model_service in model_services:
            tag = model_service.__model_tag__
            prompt_path = self.prompt_root / f"{tag}.yaml"
            self.model_services[tag] = model_service(
                base_url=settings.GPT_BASE_URL,
                api_key=settings.GPT_API_KEY,
                prompt_path=prompt_path,
            )
            if self.model_services[tag].active:
                logger.info(f"已注册模型：{tag}")
            else:
                logger.warning(f"已注册模型：{tag} [未激活 模型不可用]")

    def get(self, model_tag: str) -> OpenAIBase | None:
        return self.model_services.get(model_tag, None)


llm_registrar = LLMRegistrar(prompt_root=Path(settings.CONFIG_ROOT) / "prompts")
