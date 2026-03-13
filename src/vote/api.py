from datetime import datetime, UTC
from typing import List

from django.db import IntegrityError
from ninja import Header, Router
from ninja.errors import AuthorizationError, ValidationError, HttpError

from vote.schemas import (
    BallotSchema,
    BallotSubmission,
    EventCreationResponse,
    EventDetails,
    EventCreation,
    EventStatusUpdateBody,
)
from .models import Event, Ballot
from django.shortcuts import aget_object_or_404
import uuid

router = Router()


@router.post("/event/create", response={201: EventCreationResponse}, tags=["event"])
async def create_event(request, payload: EventCreation):
    event = Event(
        name=payload.name,
        choices=payload.choices,
        electoral_system=payload.electoral_system,
    )
    await event.asave()

    return 201, event


@router.get("/event/{event_id}", response=EventDetails, tags=["event"])
async def read_event(
    request, event_id: int, token: uuid.UUID = Header(alias="X-API-Key")
):
    event = await aget_object_or_404(Event, pk=event_id)

    if (
        token != event.share_token
        and token != event.host_token
        and token not in [x.token async for x in event.ballot_set.all()]
    ):
        raise AuthorizationError

    return event


@router.patch("/event/{event_id}/update-status", tags=["event"])
async def update_event_status(
    request,
    event_id: str,
    body: EventStatusUpdateBody,
    token: uuid.UUID = Header(alias="X-API-Key"),
):
    event = await aget_object_or_404(Event, pk=event_id)

    if token != event.host_token:
        raise AuthorizationError

    event.status = body.status

    if event.status == event.STATUS_CHOICES.CLOSED:
        event.closed = datetime.now(tz=UTC)
    else:
        event.closed = None

    await event.asave()


@router.post("/event/{event_id}/close", tags=["event"])
async def close_event(
    request, event_id: str, token: uuid.UUID = Header(alias="X-API-Key")
):
    event = await aget_object_or_404(Event, pk=event_id)

    if token != event.host_token:
        raise AuthorizationError

    event.closed = datetime.now(tz=UTC)
    event.status = event.STATUS_CHOICES.CLOSED
    await event.asave()


@router.post("/event/{event_id}/open", tags=["event"])
async def open_event(
    request, event_id: str, token: uuid.UUID = Header(alias="X-API-Key")
):
    event = await aget_object_or_404(Event, pk=event_id)

    if token != event.host_token:
        raise AuthorizationError

    event.closed = None
    event.status = event.STATUS_CHOICES.VOTING
    await event.asave()


@router.post("/event/{event_id}/show-results", tags=["event"])
async def show_results(
    request, event_id: str, token: uuid.UUID = Header(alias="X-API-Key")
):
    event = await aget_object_or_404(Event, pk=event_id)

    if token != event.host_token:
        raise AuthorizationError

    event.show_results = True
    await event.asave()


@router.post("/event/{event_id}/hide-results", tags=["event"])
async def hide_results(
    request, event_id: str, token: uuid.UUID = Header(alias="X-API-Key")
):
    event = await aget_object_or_404(Event, pk=event_id)

    if token != event.host_token:
        raise AuthorizationError

    event.show_results = False
    await event.asave()


# Ballots
@router.get("/event/{event_id}/ballots", response=List[BallotSchema], tags=["ballot"])
async def list_ballots(
    request, event_id: str, token: uuid.UUID = Header(alias="X-API-Key")
):
    event = await aget_object_or_404(Event, pk=event_id)

    if token != event.host_token and token not in [
        x.token async for x in event.ballot_set.all()
    ]:
        raise AuthorizationError

    if token != event.host_token and (
        event.status != "CL" or (event.status == "CL" and event.show_results is False)
    ):
        raise AuthorizationError

    return [x async for x in event.ballot_set.all().order_by("created", "submitted")]


@router.post("/event/{event_id}/create-ballot", tags=["ballot"])
async def create_ballot(
    request,
    event_id: str,
    voter_name: str,
    share_token: uuid.UUID = Header(alias="X-API-Key"),
):
    event = await aget_object_or_404(Event, pk=event_id)

    if share_token != event.share_token:
        raise AuthorizationError

    if event.status != "RE":
        raise HttpError(409, "Cannot create ballot at this time")

    ballot = Ballot(event=event, voter_name=voter_name)

    try:
        await ballot.asave()
    except IntegrityError as err:
        if "unique_voter_names_in_event" in str(err):
            raise ValidationError("Duplicate voter name")
        else:
            raise err

    return {"ballot_id": ballot.id, "ballot_token": ballot.token}


@router.post("/ballot/{ballot_id}/submit", response=BallotSchema, tags=["ballot"])
async def submit_ballot(
    request,
    ballot_id: int,
    payload: BallotSubmission,
    token: uuid.UUID = Header(alias="X-API-Key"),
):
    ballot = await aget_object_or_404(
        Ballot.objects.prefetch_related("event"), pk=ballot_id
    )

    if ballot.event.status != "VO":
        raise HttpError(409, "Event is not accepting ballots.")

    if token != ballot.token:
        raise AuthorizationError

    if ballot.submitted is not None:
        raise HttpError(409, "Ballot already submitted.")

    ballot.vote = payload.vote
    ballot.submitted = datetime.now(tz=UTC)
    await ballot.asave()

    return ballot


@router.get("/ballot/{ballot_id}", response=BallotSchema, tags=["ballot"])
async def get_ballot(
    request, ballot_id: int, token: uuid.UUID = Header(alias="X-API-Key")
):
    ballot = await aget_object_or_404(
        Ballot.objects.prefetch_related("event"), pk=ballot_id
    )

    if token != ballot.token and token != ballot.event.host_token:
        raise AuthorizationError

    return ballot
