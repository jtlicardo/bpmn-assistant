from typing import List, Optional, Union, Dict, Any

from pydantic import BaseModel, RootModel
from typing_extensions import Literal

TaskType = Literal["task", "userTask", "serviceTask"]


class MessageItem(BaseModel):
    """
    A message item used for LLM API communication.
    """

    role: str
    content: str
    image_url: Optional[str] = None


class BPMNTask(BaseModel):
    """
    Represents a BPMN task.
    'type' must be one of: 'task', 'userTask', or 'serviceTask'.
    """

    type: TaskType
    id: str
    label: str


EventType = Literal["startEvent", "endEvent"]


class BPMNEvent(BaseModel):
    """
    Represents a BPMN event.
    'type' must be one of: 'startEvent', 'endEvent'.
    """

    type: EventType
    id: str


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


class ParallelGateway(BaseModel):
    """
    Represents a BPMN parallel gateway.
    - 'branches': an array of arrays, each of which holds a list of BPMN elements
      to be executed in parallel.
    """

    type: Literal["parallelGateway"]
    id: str
    branches: List[List["BPMNElement"]]


BPMNElement = Union[BPMNTask, BPMNEvent, ExclusiveGateway, ParallelGateway]


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