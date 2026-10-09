from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from commands.status import CommandStatus


@dataclass(slots=True, kw_only=True)
class Command:

    timestamp: datetime

    source: str

    id: str = field(default_factory=lambda: str(uuid4()))

    status: CommandStatus = CommandStatus.PENDING