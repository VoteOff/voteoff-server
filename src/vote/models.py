import uuid
from django.db import models
from django.db.models import UniqueConstraint


class Event(models.Model):
    class STATUS_CHOICES(models.TextChoices):
        REGISTERING = "RE", "Registering"
        VOTING = "VO", "Voting"
        CLOSED = "CL", "Closed"

    share_token = models.UUIDField(default=uuid.uuid4, editable=False)
    host_token = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField()
    choices = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    show_results = models.BooleanField(default=False)
    closed = models.DateTimeField(null=True)
    electoral_system = models.CharField(max_length=2)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default="RE")


class Ballot(models.Model):
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    voter_name = models.CharField()
    created = models.DateTimeField(auto_now_add=True)
    vote = models.JSONField(null=True)
    submitted = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["voter_name", "event"], name="unique_voter_names_in_event"
            ),
        ]
