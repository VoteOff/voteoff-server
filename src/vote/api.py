from datetime import datetime
from typing import List

from django.http import HttpRequest
from ninja import Router, Query
from ninja.errors import AuthorizationError, ValidationError
from .models import Event, Ballot
from django.shortcuts import get_object_or_404
from ninja import Schema

router = Router()


class EventCreation(Schema):
    name: str
    choices: List[str]
    electoral_system: Event.ElectoralSystem


class EventDetails(Schema):
    name: str
    choices: List[str]
    electoral_system: str
    closed: datetime | None


class TokenBody(Schema):
    token: str


@router.post("/event/create")
def create_event(request: HttpRequest, payload: EventCreation):
    event = Event.objects.create(
        name=payload.name,
        choices=payload.choices,
        electoral_system=payload.electoral_system.value,
    )
    return {"id": event.id, "event_token": event.token}


@router.get("/event/{event_id}", response=EventDetails)
def read_event(request: HttpRequest, event_id: str):
    return get_object_or_404(Event, pk=event_id)


@router.post("/event/{event_id}/close")
def close_event(request: HttpRequest, event_id: str, payload: TokenBody):
    event = get_object_or_404(Event, pk=event_id)

    if payload.token != str(event.token):  # event.token is <class 'uuid.UUID'>
        raise AuthorizationError

    event.closed = datetime.now()
    event.save()


@router.post("/event/{event_id}/open")
def open_event(request: HttpRequest, event_id: str, payload: TokenBody):
    event = get_object_or_404(Event, pk=event_id)

    if payload.token != str(event.token):  # event.token is <class 'uuid.UUID'>
        raise AuthorizationError

    event.closed = None
    event.save()


# Ballots


@router.post("/event/{event_id}/create-ballot")
def create_ballot(request: HttpRequest, event_id: str, voter_name: Query[str]):
    event = get_object_or_404(Event, pk=event_id)
    ballot = Ballot.objects.create(event=event, voter_name=voter_name)
    return {"ballot_id": ballot.id, "ballot_token": ballot.token}


class BallotSubmission(Schema):
    token: str
    vote: str | List[str]


@router.post("/ballot/{ballot_id}/submit")
def submit_ballot(request: HttpRequest, ballot_id: int, payload: BallotSubmission):
    ballot = get_object_or_404(Ballot, pk=ballot_id)
    if payload.token != str(ballot.token):
        raise AuthorizationError

    # Format Validation

    if ballot.event.electoral_system == Event.ElectoralSystem.PLURALITY:
        if not isinstance(payload.vote, str):
            raise ValidationError("Ballot format does not match electoral system.")
        if payload.vote not in ballot.event.choices:
            raise ValidationError("Invalid candidate")

    elif ballot.event.electoral_system == Event.ElectoralSystem.RANKED_CHOICE:
        if not isinstance(payload.vote, List):
            raise ValidationError("Ballot format does not match electoral system.")
        for choice in payload.vote:
            if choice not in ballot.event.choices:
                raise ValidationError("Invalid candidate")

    ballot.vote = payload.vote
    ballot.submitted = datetime.now()
