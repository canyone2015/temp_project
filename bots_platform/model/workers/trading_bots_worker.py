from threading import RLock


from bots_platform.model.workers import Worker


class TradingBotsWorker(Worker):
    def __init__(self):
        super().__init__()
        self._lock: RLock = RLock()
