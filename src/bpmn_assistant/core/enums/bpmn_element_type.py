from enum import Enum


class BPMNElementType(Enum):
    TASK = "task"
    USER_TASK = "userTask"
    SERVICE_TASK = "serviceTask"
    SEND_TASK = "sendTask"
    RECEIVE_TASK = "receiveTask"
    BUSINESS_RULE_TASK = "businessRuleTask"
    MANUAL_TASK = "manualTask"
    SCRIPT_TASK = "scriptTask"
    EXCLUSIVE_GATEWAY = "exclusiveGateway"
    INCLUSIVE_GATEWAY = "inclusiveGateway"
    PARALLEL_GATEWAY = "parallelGateway"
    START_EVENT = "startEvent"
    END_EVENT = "endEvent"
    INTERMEDIATE_THROW_EVENT = "intermediateThrowEvent"
    INTERMEDIATE_CATCH_EVENT = "intermediateCatchEvent"


class EventDefinitionType(Enum):
    """Event definition types for BPMN events"""
    TIMER = "timerEventDefinition"
    MESSAGE = "messageEventDefinition"
    SIGNAL = "signalEventDefinition"
    ERROR = "errorEventDefinition"
    ESCALATION = "escalationEventDefinition"
    CONDITIONAL = "conditionalEventDefinition"
    LINK = "linkEventDefinition"
    TERMINATE = "terminateEventDefinition"
    COMPENSATION = "compensateEventDefinition"
    NONE = None  # For events without definitions
