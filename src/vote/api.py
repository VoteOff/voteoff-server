from datetime import datetime, UTC
from typing import List

from django.db import IntegrityError
from django.http import Http404, HttpRequest
from ninja import Router
from ninja.errors import AuthorizationError, ValidationError

from vote.schemas import (
    BallotSchema,
    BallotSubmission,
    EventCreationResponse,
    EventDetails,
    EventCreation,
)
from .models import Event, Ballot
from django.shortcuts import get_object_or_404
import uuid

router = Router()


@router.post("/event/create", response={201: EventCreationResponse}, tags=["event"])
def create_event(request, payload: EventCreation):
    event = Event.objects.create(
        name=payload.name,
        choices=payload.choices,
        electoral_system=payload.electoral_system,
    )
    return 201, event


@router.get("/event/{event_id}", response=EventDetails, tags=["event"])
def read_event(request, event_id: int, token: str = None):
    event = get_object_or_404(Event, pk=event_id)

    # Must provide a valid token, this can be host/share/ballot
    if token is None:
        raise AuthorizationError

    if (
        token != str(event.share_token)
        and token != str(event.host_token)
        and token not in [str(x.token) for x in event.ballot_set.all()]
    ):
        raise AuthorizationError

    return event


@router.post("/event/{event_id}/close", tags=["event"])
def close_event(request: HttpRequest, event_id: str, host_token: str):
    event = get_object_or_404(Event, pk=event_id)

    if host_token != str(event.host_token):
        raise AuthorizationError

    event.closed = datetime.now()
    event.save()


@router.post("/event/{event_id}/open", tags=["event"])
def open_event(request: HttpRequest, event_id: str, host_token: str):
    event = get_object_or_404(Event, pk=event_id)

    if host_token != str(event.host_token):
        raise AuthorizationError

    event.closed = None
    event.save()


# Ballots
@router.get("/event/{event_id}/ballots", response=List[BallotSchema], tags=["ballot"])
def list_ballots(request, event_id: str, token: str):
    event = get_object_or_404(Event, pk=event_id)

    if token != str(event.host_token) and token not in [
        str(x.token) for x in event.ballot_set.all()
    ]:
        raise AuthorizationError

    return event.ballot_set.all().order_by("created", "submitted")


@router.post("/event/{event_id}/create-ballot", tags=["ballot"])
def create_ballot(
    request: HttpRequest, event_id: str, voter_name: str, share_token: str
):
    event = get_object_or_404(Event, pk=event_id)

    if share_token != str(event.share_token):
        raise AuthorizationError

    try:
        ballot = Ballot.objects.create(event=event, voter_name=voter_name)
    except IntegrityError as err:
        if "unique_voter_names_in_event" in str(err):
            raise ValidationError("Duplicate voter name")
        else:
            raise err

    return {"ballot_id": ballot.id, "ballot_token": ballot.token}


@router.post("/ballot/{ballot_id}/submit", tags=["ballot"])
def submit_ballot(
    request: HttpRequest, ballot_id: int, token: str, payload: BallotSubmission
):
    ballot = get_object_or_404(Ballot, pk=ballot_id)
    if token != str(ballot.token):
        raise AuthorizationError

    if ballot.submitted is not None:
        raise AuthorizationError

    ballot.vote = payload.vote
    ballot.submitted = datetime.now(tz=UTC)
    ballot.save()


@router.get("/ballot/from-token", response=BallotSchema, tags=["ballot"])
def get_ballot_form_token(request: HttpRequest, token: uuid.UUID):
    ballots = Ballot.objects.filter(token=token)

    if ballots.count() == 0:
        raise Http404("Ballot not found")
    else:
        return ballots.first()


@router.get("/ballot/{ballot_id}", response=BallotSchema, tags=["ballot"])
def get_ballot(request, ballot_id: int, token: uuid.UUID):
    ballot = get_object_or_404(Ballot, pk=ballot_id)

    if token != ballot.token and token != ballot.event.host_token:
        raise AuthorizationError

    return ballot
