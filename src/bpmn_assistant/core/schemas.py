from typing import List, Optional, Union, Dict, Any

from pydantic import BaseModel, RootModel
from typing_extensions import Literal

TaskType = Literal["task", "userTask", "serviceTask", "sendTask", "receiveTask", "businessRuleTask", "manualTask", "scriptTask"]


class MessageImage(BaseModel):
    """
    Represents an image attached to a message.
    """

    preview: str  # Base64 encoded image data URL
    name: str  # Original filename


class MessageItem(BaseModel):
    """
    A message item used for LLM API communication.
    Supports text content and optional images for vision-enabled models.
    """

    role: str
    content: str
    images: Optional[List[MessageImage]] = None


class BPMNTask(BaseModel):
    """
    Represents a BPMN task.
    'type' must be one of: 'task', 'userTask', 'serviceTask', 'sendTask', 'receiveTask', 'businessRuleTask', 'manualTask', or 'scriptTask'.
    """

    type: TaskType
    id: str
    label: str


EventType = Literal["startEvent", "endEvent", "intermediateThrowEvent", "intermediateCatchEvent"]
EventDefinitionType = Literal["timerEventDefinition", "messageEventDefinition"]


class BPMNEvent(BaseModel):
    """
    Represents a BPMN event.
    'type' must be one of: 'startEvent', 'endEvent', 'intermediateThrowEvent', 'intermediateCatchEvent'.
    'eventDefinition' is optional and specifies the event type (timer, message, etc.)
    """

    type: EventType
    id: str
    label: Optional[str] = None
    eventDefinition: Optional[EventDefinitionType] = None


class ExclusiveGatewayBranch(BaseModel):
    """
    Represents a branch of an exclusive gateway.
    - 'condition': textual condition for the branch
    - 'path': array of BPMN elements executed if the condition is met
    - 'next': optional ID of the next element (if not following default sequence)
    """

    condition: str
    path: List["BPMNElement"] = []
    next: Optional[str] = None


class ExclusiveGateway(BaseModel):
    """
    Represents a BPMN exclusive gateway.
    - 'has_join': indicates whether this gateway also merges paths
    - 'branches': list of exclusive branches
    """

    type: Literal["exclusiveGateway"]
    id: str
    label: str
    has_join: bool
    branches: List[ExclusiveGatewayBranch]


class InclusiveGatewayBranch(BaseModel):
    """
    Represents a branch of an inclusive gateway.
    - 'condition': textual condition for the branch (not required for default branches)
    - 'path': array of BPMN elements executed if the condition is met
    - 'next': optional ID of the next element (if not following default sequence)
    - 'is_default': marks this branch as the default (taken when no conditions are met)
    """

    condition: Optional[str] = None
    path: List["BPMNElement"] = []
    next: Optional[str] = None
    is_default: bool = False


class InclusiveGateway(BaseModel):
    """
    Represents a BPMN inclusive gateway (OR-gateway).
    Multiple branches can be taken simultaneously based on their conditions.
    - 'has_join': indicates whether this gateway also merges paths
    - 'branches': list of inclusive branches (can have multiple conditions fulfilled)
    """

    type: Literal["inclusiveGateway"]
    id: str
    label: str
    has_join: bool
    branches: List[InclusiveGatewayBranch]


class ParallelGateway(BaseModel):
    """
    Represents a BPMN parallel gateway.
    - 'branches': an array of arrays, each of which holds a list of BPMN elements
      to be executed in parallel.
    """

    type: Literal["parallelGateway"]
    id: str
    branches: List[List["BPMNElement"]]


BPMNElement = Union[BPMNTask, BPMNEvent, ExclusiveGateway, InclusiveGateway, ParallelGateway]


class ProcessModel(BaseModel):
    """
    Represents a BPMN process containing a list of elements
    that can be tasks, events, or gateways.
    """

    process: List[BPMNElement]


class EditProposal(BaseModel):
    """
    Represents an edit proposal for a BPMN process.
    """

    function: str
    arguments: Dict[str, Any]


class StopSignal(BaseModel):
    """
    Represents a stop signal for the BPMN editing process.
    """

    stop: Literal[True]

IntermediateEditProposal = RootModel[Union[EditProposal, StopSignal]]
