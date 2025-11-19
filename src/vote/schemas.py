from datetime import datetime
from typing import Any, List
import uuid
from ninja import ModelSchema, Schema

from vote.models import Ballot


class EventCreation(Schema):
    name: str
    choices: List[str]
    electoral_system: str


class EventDetails(EventCreation):
    id: int
    closed: datetime | None
    share_token: uuid.UUID


class EventCreationResponse(EventDetails):
    host_token: uuid.UUID


class BallotSchema(ModelSchema):
    class Meta:
        model = Ballot
        fields = ["id", "voter_name", "vote", "created", "submitted"]


class BallotSubmission(Schema):
    vote: Any
