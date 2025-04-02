from .llm_manager.llm_registrar import llm_registrar
from .res_manager.news_capturer import news_loader
from .res_manager.jm_capturer import jm_loader
from .res_manager.random_pic_capturer import random_pic_loader

__all__ = ["llm_registrar", "news_loader", "jm_loader", "random_pic_loader"]
