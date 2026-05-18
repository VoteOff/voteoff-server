from datetime import datetime
from typing import Any, List, Literal
import uuid
from ninja import ModelSchema, Schema

from vote.models import Ballot

type EventStatus = Literal["RE", "CL", "VO"]


class EventStatusUpdateBody(Schema):
    allow_registration: bool | None = None
    allow_voting: bool | None = None


class EventCreation(Schema):
    name: str
    choices: List[str]
    electoral_system: str
    allow_registration: bool = False
    allow_voting: bool = False


class EventDetails(EventCreation):
    id: int
    closed: datetime | None
    allow_registration: bool
    allow_voting: bool
    share_token: uuid.UUID
    show_results: bool


class EventCloseResponse(Schema):
    closed: datetime


class EventCreationResponse(EventDetails):
    host_token: uuid.UUID


class BallotSchema(ModelSchema):
    class Meta:
        model = Ballot
        fields = ["id", "voter_name", "vote", "created", "submitted"]


class BallotSubmission(Schema):
    vote: Any
