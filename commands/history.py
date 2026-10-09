from collections import deque


class CommandHistory:

    def __init__(self, size=100):

        self.history = deque(maxlen=size)

    def add(self, command):

        self.history.append(command)

    def last(self):

        if self.history:

            return self.history[-1]

        return None

    def all(self):

        return list(self.history)