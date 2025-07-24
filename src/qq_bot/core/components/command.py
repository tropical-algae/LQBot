import subprocess
import shlex
from qq_bot.base import ComponentBase
from qq_bot.utils.decorator import require_active
from qq_bot.utils.util import load_yaml
from qq_bot.utils.config import settings
from qq_bot.utils.logger import logger


class CommandProvider(ComponentBase):
    __component_name__ = settings.COMMAND_COMPONENT_NAME
    
    def __init__(self, filepath: str):
        super().__init__(filepath=filepath)
        self.command_config = load_yaml(filepath)
        if not self.command_config:
            self.activate(False)

    @require_active
    def _command_actived(self, command: str) -> bool:
        args = shlex.split(command)
        if not args:
            return False
        
        base_cmd = args[0]
        sub_args = args[1:]
        
        cmd_rule = self.command_config.get(base_cmd, None)
        if not cmd_rule:
            return False  # 未配置的命令默认禁止

        blocked = set(cmd_rule.get('blacklist', []))
        for arg in sub_args:
            if any(arg.startswith(blocked_arg) for blocked_arg in blocked):
                return False
        return True

    @require_active
    def execute_command(self, command: str):
        if self._command_actived(command):
            try:
                result = subprocess.run(shlex.split(command), capture_output=True, text=True)
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                logger.warning(f"命令执行失败: {e.stderr}")
        else:
            logger.warning("该命令不被允许执行。")

command_runner = CommandProvider(settings.COMMAND_CONFIG_FILE)
