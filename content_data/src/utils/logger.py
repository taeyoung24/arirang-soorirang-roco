import asyncio
import colorama
import re
from datetime import datetime
from typing import Optional, Literal

# colorama 초기화
colorama.init(autoreset=True)

def convert_markdown_bold(text: str) -> str:
    # **로 감싸진 부분을 볼드체로 변환
    return re.sub(r"\*\*(.*?)\*\*", f"{colorama.Style.BRIGHT}\\1{colorama.Style.RESET_ALL}", text)

# ============================= SINGLETON OBJECT =============================
# ============================= SINGLETON OBJECT =============================
class Logger:
    def __init__(self, name: str="BOT"):
        self.name = name
        self._log_config = {
            "DEBUG": {"level": -1, "color": colorama.Fore.BLUE},
            "INFO": {"level": 0, "color": colorama.Fore.GREEN},
            "SUCCESS": {"level": 0, "color": colorama.Fore.GREEN},
            "WARNING": {"level": 1, "color": colorama.Fore.YELLOW},
            "ERROR": {"level": 2, "color": colorama.Fore.RED},
            "CRITICAL": {"level": 3, "color": colorama.Back.RED}
        }


    def log(self, content: str, log_type: str = "INFO", datestr: Optional[str]=None, hide_prompt=False):
        if datestr is None: datestr = datetime.now().strftime("%y.%m.%d %H:%M:%S")
        if log_type not in self._log_config:
            self.log(f"Invalid log type used: {log_type}", "WARNING")
            log_type = "INFO"
        
        config = self._log_config[log_type]
        reset_code = colorama.Style.RESET_ALL
        bold_code = colorama.Style.BRIGHT
        
        terminal_content = f"{bold_code}{config['color']}{log_type:>8}:   {reset_code} {datestr}   {convert_markdown_bold(content)}"
        if not hide_prompt: print(terminal_content)

    def debug(self, content: str, datestr: Optional[str]=None, hide_prompt=False):
        self.log(content, "DEBUG", datestr, hide_prompt)


    def info(self, content: str, datestr: Optional[str]=None, hide_prompt=False):
        self.log(content, "INFO", datestr, hide_prompt)


    def success(self, content: str, datestr: Optional[str]=None, hide_prompt=False):
        self.log(content, "SUCCESS", datestr, hide_prompt)


    def warning(self, content: str, datestr: Optional[str]=None, hide_prompt=False):
        self.log(content, "WARNING", datestr, hide_prompt)
        
    def error(self, content: str, datestr: Optional[str]=None, hide_prompt=False):
        self.log(content, "ERROR", datestr, hide_prompt)
        
    def critical(self, content: str, datestr: Optional[str]=None, hide_prompt=False):
        self.log(content, "CRITICAL", datestr, hide_prompt)

logger = Logger()
