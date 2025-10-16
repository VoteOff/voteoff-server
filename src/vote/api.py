from datetime import datetime
from typing import List, Any

from django.http import HttpRequest
from ninja import Router
from ninja.errors import AuthorizationError, ValidationError
from .models import Event, Ballot
from django.shortcuts import get_object_or_404
from ninja import Schema
import uuid

router = Router()


class EventCreation(Schema):
    name: str
    choices: List[str]
    electoral_system: Event.ElectoralSystem


class EventDetails(EventCreation):
    id: int
    closed: datetime | None
    share_token: uuid.UUID


class EventCreationResponse(EventDetails):
    host_token: uuid.UUID


@router.post("/event/create", response={201: EventCreationResponse})
def create_event(request, payload: EventCreation):
    event = Event.objects.create(
        name=payload.name,
        choices=payload.choices,
        electoral_system=payload.electoral_system.value,
    )
    return 201, event


@router.get("/event/{event_id}", response=EventDetails)
def read_event(request, event_id: int, host_token: str = None, share_token: str = None):
    event = get_object_or_404(Event, pk=event_id)

    # Must provide a valid host_token or share_token
    if share_token is None and host_token is None:
        raise AuthorizationError
    if share_token is not None and share_token != str(event.share_token):
        raise AuthorizationError
    if host_token is not None and host_token != str(event.host_token):
        raise AuthorizationError

    return event


@router.post("/event/{event_id}/close")
def close_event(request: HttpRequest, event_id: str, host_token: str):
    event = get_object_or_404(Event, pk=event_id)

    if host_token != str(event.host_token):
        raise AuthorizationError

    event.closed = datetime.now()
    event.save()


@router.post("/event/{event_id}/open")
def open_event(request: HttpRequest, event_id: str, host_token: str):
    event = get_object_or_404(Event, pk=event_id)

    if host_token != str(event.host_token):
        raise AuthorizationError

    event.closed = None
    event.save()


@router.get("/event/{event_id}/ballot-statuses")
def get_ballot_statuses(request: HttpRequest, event_id: str, host_token: str):
    event = get_object_or_404(Event, pk=event_id)

    if host_token != str(event.host_token):
        raise AuthorizationError

    return {
        'pending': [b.voter_name for b in event.ballot_set.filter(submitted__isnull=True).order_by('created')],
        'submitted': [b.voter_name for b in event.ballot_set.filter(submitted__isnull=False).order_by('submitted')]
    }


@router.get("/event/{event_id}/ballot-results")
def get_ballot_results(request: HttpRequest, event_id: str, host_token: str):
    event = get_object_or_404(Event, pk=event_id)

    if host_token != str(event.host_token):
        raise AuthorizationError

    return [b.vote for b in event.ballot_set.all()]


# Ballots


@router.post("/event/{event_id}/create-ballot")
def create_ballot(
    request: HttpRequest, event_id: str, voter_name: str, share_token: str
):
    event = get_object_or_404(Event, pk=event_id)

    if share_token != str(event.share_token):
        raise AuthorizationError

    # TODO better handling of name duplicates

    ballot = Ballot.objects.create(event=event, voter_name=voter_name)
    return {"ballot_id": ballot.id, "ballot_token": ballot.token}


class BallotSubmission(Schema):
    vote: Any


@router.post("/ballot/{ballot_id}/submit")
def submit_ballot(request: HttpRequest, ballot_id: int, token: str, payload: BallotSubmission):
    ballot = get_object_or_404(Ballot, pk=ballot_id)
    if token != str(ballot.token):
        raise AuthorizationError

    ballot.vote = payload.vote
    ballot.submitted = datetime.now()


