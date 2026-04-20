# app/core/executor_wrapper.py
"""
Custom wrapper untuk ProcessPoolExecutor dengan tracking
"""
from concurrent.futures import ProcessPoolExecutor, Future
import threading
from typing import Dict, Optional
import uuid


class TrackedProcessPoolExecutor:
    """
    Wrapper untuk ProcessPoolExecutor dengan task tracking
    ✅ Thread-safe, compatible dengan FastAPI
    """
    
    def __init__(self, max_workers: int):
        self._executor = ProcessPoolExecutor(max_workers=max_workers)
        self._tasks: Dict[str, Future] = {}
        self._lock = threading.Lock()
        self._max_workers = max_workers
    
    def submit(self, fn, *args, **kwargs) -> tuple[str, Future]:
        """Submit task dan return task_id + future"""
        task_id = str(uuid.uuid4())[:8]
        future = self._executor.submit(fn, *args, **kwargs)
        
        with self._lock:
            self._tasks[task_id] = future
        
        # Cleanup completed tasks automatically
        future.add_done_callback(lambda f: self._cleanup(task_id))
        
        return task_id, future
    
    def _cleanup(self, task_id: str):
        """Hapus task yang sudah selesai dari tracking"""
        with self._lock:
            self._tasks.pop(task_id, None)
    
    def get_stats(self) -> dict:
        """Get executor statistics"""
        with self._lock:
            active = sum(1 for f in self._tasks.values() if not f.done())
            pending = len(self._tasks) - active
        
        return {
            "max_workers": self._max_workers,
            "active_tasks": active,
            "pending_tasks": pending,
            "total_tracked": len(self._tasks),
            "available_slots": max(0, self._max_workers - active)
        }
    
    def shutdown(self, wait: bool = True, **kwargs):
        """Shutdown executor"""
        self._executor.shutdown(wait=wait, **kwargs)
    
    # Delegate other methods to underlying executor
    def __getattr__(self, name):
        return getattr(self._executor, name)