import time
import uuid
from enum import Enum
from typing import Any, Callable, Dict, List
from pydantic import BaseModel, Field


class PipelineEventType(Enum):
    """
    Defines the types of events that can be emitted during pipeline execution.
    """
    STARTED = "STARTED"
    STAGE_STARTED = "STAGE_STARTED"
    STAGE_COMPLETED = "STAGE_COMPLETED"
    RETRIEVAL_COMPLETED = "RETRIEVAL_COMPLETED"
    PROMPT_GENERATED = "PROMPT_GENERATED"
    LLM_COMPLETED = "LLM_COMPLETED"
    REVIEW_GENERATED = "REVIEW_GENERATED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PipelineEvent(BaseModel):
    """
    Represents an event emitted by the RAG pipeline.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: PipelineEventType
    timestamp: float = Field(default_factory=time.time)
    stage_name: str
    request_id: str
    data: dict[str, Any] = Field(default_factory=dict)


class PipelineEventBus:
    """
    A simple event bus to subscribe to and emit pipeline events.
    """
    def __init__(self) -> None:
        self._subscribers: Dict[PipelineEventType, List[Callable[[PipelineEvent], None]]] = {}

    def subscribe(self, event_type: PipelineEventType, listener: Callable[[PipelineEvent], None]) -> None:
        """
        Subscribe a listener to a specific pipeline event type.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(listener)

    def emit(self, event: PipelineEvent) -> None:
        """
        Emit a pipeline event to all subscribed listeners.
        """
        if event.event_type in self._subscribers:
            for listener in self._subscribers[event.event_type]:
                listener(event)
