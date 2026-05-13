import threading
import importlib
import queue

class SpeculationEngine:
    def __init__(self):
        self.module_queue = queue.Queue()
        self.thread = threading.Thread(target=self._process_load, daemon=True)
        self.is_started = False

    def start(self):
        if not self.is_started:
            self.thread.start()
            self.is_started = True

    def register_module(self, fullname):
        self.module_queue.put(fullname)

    def _process_load(self):
        while True:
            modulo = self.module_queue.get()
            try:
                importlib.import_module(modulo)
            except Exception:
                pass
            finally:
                self.module_queue.task_done()
