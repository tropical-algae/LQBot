from lqbot.utils.logger import logger
from ncatbot.utils import get_log


logger = get_log()



class ComponentBase:
    __component_name__: str | None = None

    def __init__(self, *args, **kwargs) -> None:
        has_meaningful_args: bool = True
        
        if (kwargs and not all(kwargs.values())) or (args and not all(args)):
            has_meaningful_args = False
        self.activate(has_meaningful_args)

    def activate(self, active: bool) -> None:
        self.active = active
        if active:
            logger.info(f"{self.__component_name__ or 'Component'} activated")
        else:
            logger.warning(f"{self.__component_name__ or 'Component'} not activated")
