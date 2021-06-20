import time
import typing
from abc import ABC, abstractmethod

from django.db import models
from pydantic import BaseModel, Field, validator


class Event(BaseModel):
    name: str = ""
    timestamp: float = Field(default_factory=time.time)
    comment: str = ""

    @validator("name", always=True)
    def reset_name(cls, v):
        return cls.event_id()

    @classmethod
    def event_id(cls):
        return cls.__name__


class DonationApprovedEvent(Event):
    pass


class DonationDispatchedEvent(Event):
    pass


class DonationDeliveredEvent(Event):
    pass


class DonationCancelledEvent(Event):
    pass


class State(ABC):
    @abstractmethod
    def apply(self, event: Event) -> "State":
        raise NotImplementedError()

    @classmethod
    def state_id(cls) -> str:
        return cls.__name__


class InvalidState(State):
    def apply(self, event: Event) -> State:
        return InvalidState()


class CancelledState(State):
    def apply(self, event: Event) -> State:
        return CancelledState()


class CollectingState(State):
    def apply(self, event: Event) -> State:
        return CancelledState()


class PendingApprovalState(State):
    def apply(self, event: Event) -> State:
        if event.name == DonationApprovedEvent.event_id():
            return PendingDispatchState()
        elif event.name == DonationCancelledEvent.event_id():
            return CancelledState()
        else:
            return InvalidState()


class PendingDispatchState(State):
    def apply(self, event: Event) -> State:
        if event.name == DonationDispatchedEvent.event_id():
            return DoneState()
            # return PendingDeliveryState()
        elif event.name == DonationCancelledEvent.event_id():
            return CancelledState()
        else:
            return InvalidState()


class PendingDeliveryState(State):
    def apply(self, event: Event) -> State:
        if event.name == DonationDeliveredEvent.event_id():
            return DoneState()
        else:
            return InvalidState()


class DoneState(State):
    def apply(self, event: Event) -> State:
        return InvalidState()


class DonationStateMachine:
    def __init__(self, init_state: State = None) -> None:
        if init_state is None:
            self.current_state = PendingApprovalState()
        else:
            self.current_state = init_state

    def run_all(self, events: typing.List[Event]):
        for e in events:
            self.current_state = self.current_state.apply(e)


events = {
    DonationApprovedEvent.event_id(): DonationApprovedEvent,
    DonationDeliveredEvent.event_id(): DonationDeliveredEvent,
    DonationCancelledEvent.event_id(): DonationCancelledEvent,
    DonationDispatchedEvent.event_id(): DonationDispatchedEvent,
}

organization_events = (
    DonationApprovedEvent,
    DonationDeliveredEvent,
    DonationCancelledEvent,
)

donator_events = (DonationDispatchedEvent, DonationCancelledEvent)

EventEnum = models.TextChoices("EventEnum", " ".join(events.keys()))


def get_event(data: typing.Union[typing.Dict[str, typing.Any], Event]) -> Event:
    if isinstance(data, Event):
        return data
    elif data.get("name") in events:
        return events[data["name"]](**data)
    raise ValueError(f"Unknown event: {data}")


donation_states = {
    InvalidState.state_id(): InvalidState,
    CancelledState.state_id(): CancelledState,
    PendingApprovalState.state_id(): PendingApprovalState,
    PendingDispatchState.state_id(): PendingDispatchState,
    PendingDeliveryState.state_id(): PendingDeliveryState,
    DoneState.state_id(): DoneState,
}

DonationStateEnum = models.TextChoices(
    "DonationStateEnum", " ".join(donation_states.keys())
)

required_item_status = {
    InvalidState.state_id(): InvalidState,
    CancelledState.state_id(): CancelledState,
    CollectingState.state_id(): CollectingState,
    DoneState.state_id(): DoneState,
}

RequiredItemStateEnum = models.TextChoices(
    "RequiredItemStateEnum", " ".join(required_item_status.keys())
)


def get_state(name: str):
    if name in donation_states:
        return donation_states[name]()
    raise ValueError(f"Unknown state: {name}")
