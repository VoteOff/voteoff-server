import uuid
from django.db import models
from django.db.models import Case, UniqueConstraint, Value, When

status_expr = Case(
    When(allow_registration=True, allow_voting=False, then=Value("RE")),
    When(allow_registration=False, allow_voting=True, then=Value("VO")),
    When(allow_registration=False, allow_voting=False, then=Value("CL")),
    default=Value("CL"),
)


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
    allow_registration = models.BooleanField(default=False)
    allow_voting = models.BooleanField(default=False)

    @property
    def status(self):
        if self.allow_registration and not self.allow_voting:
            return self.STATUS_CHOICES.REGISTERING
        elif not self.allow_registration and self.allow_voting:
            return self.STATUS_CHOICES.VOTING
        elif not self.allow_registration and not self.allow_voting:
            return self.STATUS_CHOICES.CLOSED
        else:
            raise ValueError(
                f"Invalid combination of permissions: {self.allow_registration}, {self.allow_voting}"
            )


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
