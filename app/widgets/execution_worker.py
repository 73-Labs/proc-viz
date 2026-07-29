"""Background worker for async procedure execution."""

from PySide6.QtCore import QRunnable, Signal, QObject
from app.drivers.database_driver import ExecutionRequest, ExecutionResult
from typing import Callable, Optional


class ExecutionWorker(QRunnable):
    """Execute procedures in background thread without blocking UI."""

    class Signals(QObject):
        """Signals for execution progress and completion."""
        finished = Signal(ExecutionResult)
        error = Signal(str)

    def __init__(self, executor: Callable[[ExecutionRequest], ExecutionResult], request: ExecutionRequest):
        """Initialize worker.

        Args:
            executor: Callable that executes the request (e.g., accessor.execute_procedure)
            request: ExecutionRequest to execute
        """
        super().__init__()
        self.signals = self.Signals()
        self.executor = executor
        self.request = request

    def run(self):
        """Execute procedure in background thread."""
        try:
            result = self.executor(self.request)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
