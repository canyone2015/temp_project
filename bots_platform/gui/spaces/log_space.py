from nicegui import ui
from typing import Union
import pprint

from bots_platform.model import Logger
from bots_platform.model import TimeStamp


class LogSpace:
    def __init__(self):
        self._logger: Union[Logger, None] = None
        self._log_space = None

    async def init(self):
        if self._log_space:
            self._log_space.delete()
        self._log_space = ui.log(max_lines=1000).classes('h-96').style("width: 800px;")
        self.log_data('Started!')

    def check(self):
        if self._log_space is None or self._logger is None:
            raise Exception(f'{type(self).__name__} is not initialized')

    def set_logger(self, logger: Logger):
        if self._logger:
            self._logger.disconnect(self.log_data)
        self._logger = logger
        self._logger.connect(self.log_data)

    def log_data(self, *args, **kwargs):
        s1 = pprint.pformat('; '.join(f"{x}" for x in args)) + '\n' if args else ''
        s2 = pprint.pformat('; '.join(f"({k}:{v})" for k, v in kwargs.items())) + '\n' if kwargs else ''
        dt_str = TimeStamp.format_time(TimeStamp.get_local_dt_from_now())
        line = f'{dt_str}. {s1}{s2}\n'
        self._log_space.push(line)

    def detach(self):
        self._logger.disconnect(self.log_data)
        try:
            self._log_space.delete()
        except:
            pass
        self._log_space = None
