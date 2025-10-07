from datetime import datetime
from typing import List

from django.http import HttpRequest
from ninja import Router
from ninja.errors import AuthorizationError
from .models import Event
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
    event = Event.objects.create(name=payload.name, choices=payload.choices, electoral_system=payload.electoral_system.value)
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