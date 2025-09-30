import uuid
from django.db import models
from django.db.models import UniqueConstraint


class Event(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    token = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField()
    choices = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    closed = models.DateTimeField(null=True)

    RANKED_CHOICE = "RC"
    PLURALITY = "PL"
    ELECTORAL_SYSTEM_CHOICES = {
        RANKED_CHOICE: "Ranked Choice",
        PLURALITY: "Plurality",
    }

    electoral_system = models.CharField(max_length=2, choices=ELECTORAL_SYSTEM_CHOICES)


class Ballot(models.Model):

    token = models.UUIDField(default=uuid.uuid4, editable=False)

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    voter_name = models.CharField()
    vote = models.JSONField(null=True)
    submitted = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['voter_name', 'event'], name='unique_voter_names_in_event'),
        ]

