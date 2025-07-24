import subprocess
import shlex
from qq_bot.utils.util import load_yaml
from qq_bot.utils.config import settings


class CommandProvider:
    def __init__(self, config_path: str):
        self.command_config = load_yaml(config_path)

    def is_command_allowed(self, command: str) -> bool:
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

    def execute_command(self, command: str):
        if self.is_command_allowed(command):
            try:
                result = subprocess.run(shlex.split(command), capture_output=True, text=True)
                print(result.stdout)
            except subprocess.CalledProcessError as e:
                print(f"命令执行失败: {e.stderr}")
        else:
            print("该命令不被允许执行。")

command_runner = CommandProvider(settings.COMMAND_CONFIG_FILE)
