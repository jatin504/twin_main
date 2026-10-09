from collections import defaultdict

from commands.queue import CommandQueue
from commands.status import CommandStatus
from commands.history import CommandHistory


class CommandManager:

    def __init__(self):

        self.queues = defaultdict(CommandQueue)

        self.history = CommandHistory()

    def submit(

        self,

        target,

        command,

    ):

        command.status = CommandStatus.ACCEPTED

        self.queues[target].push(command)

    def next(

        self,

        target,

    ):

        return self.queues[target].pop()

    def has_command(

        self,

        target,

    ):

        return not self.queues[target].empty()