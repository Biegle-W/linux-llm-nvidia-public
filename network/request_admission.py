"""Fair, bounded admission for the one qualified NVIDIA inference slot.

Lifecycle controls and inference use the same gate. Nonblocking idle checks never
jump ahead of waiting clients. No backend concurrency is enabled by this queue.
"""
from collections import deque
import threading
import time


class QueueFull(Exception):
    pass


class RequestAdmission:
    def __init__(self, max_queued=8):
        if type(max_queued) is not int or max_queued < 1:
            raise ValueError('max_queued must be positive')
        self.max_queued = max_queued
        self._condition = threading.Condition()
        self._waiters = deque()
        self._held = False

    def snapshot(self):
        with self._condition:
            return {'admission_active': self._held, 'queued': len(self._waiters),
                    'max_queued': self.max_queued, 'max_inflight': 1,
                    'same_model_concurrency': False}

    def acquire(self, blocking=True, timeout=-1, progress=None):
        if timeout < 0 and timeout != -1:
            raise ValueError('Invalid admission timeout')
        deadline = None if timeout == -1 else time.monotonic() + timeout
        if progress:
            progress()
        ticket = object()
        granted = False
        with self._condition:
            if not self._held and not self._waiters:
                self._held = True
                return True
            if not blocking or timeout == 0:
                return False
            if len(self._waiters) >= self.max_queued:
                raise QueueFull('The inference request queue is full')
            self._waiters.append(ticket)
        try:
            while True:
                with self._condition:
                    remaining = None if deadline is None else deadline - time.monotonic()
                    if remaining is not None and remaining <= 0:
                        return False
                    if not self._held and self._waiters[0] is ticket:
                        self._waiters.popleft()
                        self._held = granted = True
                        return True
                    self._condition.wait(.25 if remaining is None else min(.25, remaining))
                # Connection checks may fail; always remove a cancelled ticket.
                if progress:
                    progress()
        finally:
            if not granted:
                with self._condition:
                    self._waiters.remove(ticket)
                    self._condition.notify_all()

    def release(self):
        with self._condition:
            if not self._held:
                raise RuntimeError('Admission gate is not held')
            self._held = False
            self._condition.notify_all()
