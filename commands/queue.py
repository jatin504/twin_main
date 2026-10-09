from collections import deque


class CommandQueue:

    def __init__(self):

        self._queue = deque()

    def push(self, command):

        self._queue.append(command)

    def pop(self):

        if self._queue:

            return self._queue.popleft()

        return None

    def empty(self):

        return len(self._queue) == 0

    def clear(self):

        self._queue.clear()

    def __len__(self):

        return len(self._queue)