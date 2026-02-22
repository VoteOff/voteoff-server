from datetime import datetime
from typing import Any, List, Literal
import uuid
from ninja import ModelSchema, Schema

from vote.models import Ballot

type EventStatus = Literal["RE", "CL", "VO"]


class EventStatusUpdateBody(Schema):
    status: EventStatus


class EventCreation(Schema):
    name: str
    choices: List[str]
    electoral_system: str


class EventDetails(EventCreation):
    id: int
    closed: datetime | None
    status: EventStatus
    share_token: uuid.UUID
    show_results: bool


class EventCreationResponse(EventDetails):
    host_token: uuid.UUID


class BallotSchema(ModelSchema):
    class Meta:
        model = Ballot
        fields = ["id", "voter_name", "vote", "created", "submitted"]


class BallotSubmission(Schema):
    vote: Any
