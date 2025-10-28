from enum import Enum

class CeleryStatus(Enum):
    SUCCESS = "success"
    STARTED = "started"
    FAILED = "failed"