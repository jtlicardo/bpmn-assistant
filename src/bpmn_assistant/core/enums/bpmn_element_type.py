from enum import Enum


class BPMNElementType(Enum):
    TASK = "task"
    USER_TASK = "userTask"
    SERVICE_TASK = "serviceTask"
    EXCLUSIVE_GATEWAY = "exclusiveGateway"
    PARALLEL_GATEWAY = "parallelGateway"
    START_EVENT = "startEvent"
    END_EVENT = "endEvent"
