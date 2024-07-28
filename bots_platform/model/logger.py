from pathlib import Path
from io import TextIOWrapper
from typing import Union
import pprint
import os

from bots_platform.model.utils import TimeStamp


class Logger:
    def __init__(self):
        self._listeners = list()
        self._log_dir = os.getcwd()
        self._filepath = None
        self._file: Union[TextIOWrapper, None] = None

    def __del__(self):
        if self._file:
            self._file.close()

    def connect(self, listener):
        self._listeners.append(listener)

    def disconnect(self, listener):  # no exception
        try:
            self._listeners.remove(listener)
        except:
            pass

    def log(self, *args, **kwargs):  # no exception
        try:
            date_str = TimeStamp.format_date(TimeStamp.get_local_dt_from_now()).replace('-', '_')
            filepath = Path(self._log_dir, f"{date_str}.log")
            if self._filepath != filepath or self._file is None:
                if self._file is not None and not self._file.closed:
                    self._file.close()
                    self._file = None
                self._filepath = filepath
                try:
                    self._file = open(self._filepath.absolute(), 'a', encoding='utf-8')
                    if not self._file.writable():
                        raise
                except:
                    if not self._file.closed:
                        self._file.close()
                    self._file = None
                    self._filepath = None
                    return
            s1 = pprint.pformat('; '.join(f"{x}" for x in args)) + '\n' if args else ''
            s2 = pprint.pformat('; '.join(f"({k}:{v})" for k, v in kwargs.items())) + '\n' if kwargs else ''
            dt_str = TimeStamp.format_datetime(TimeStamp.get_local_dt_from_now())
            line = f'{dt_str}. {s1}{s2}\n'
            self._file.write(line)
            for listener in self._listeners:
                try:
                    listener(*args, **kwargs)
                except BaseException as e:
                    self._file.write(f"{dt_str}. {' '.join(e.args)}\n")
            self._file.flush()
        except:
            pass
