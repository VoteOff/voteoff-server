from django.test import TestCase, Client
from ninja.testing import TestClient
from .models import Event, Ballot
from .api import router


class EventTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)
        self.event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system=Event.ElectoralSystem.PLURALITY,
        )

    def test_create_event(self):
        response = self.client.post(
            "/event/create",
            json={
                "name": "Big Cookoff",
                "choices": [
                    "Tom's Texas Chili",
                    "Jim's Vegan Chili",
                    "Ed's Fusion Chili",
                ],
                "electoral_system": "RC",
            },
        )
        self.assertEqual(response.status_code, 201)

    def test_read_event(self):
        event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system=Event.ElectoralSystem.PLURALITY,
        )
        response = self.client.get(
            f"/event/{event.id}", query_params={"host_token": str(event.host_token)}
        )
        self.assertEqual(response.status_code, 200)

    def test_read_event_without_token(self):
        event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system=Event.ElectoralSystem.PLURALITY,
        )
        response = self.client.get(
            f"/event/{event.id}"
        )
        self.assertEqual(response.status_code, 403)


class BallotTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)
        self.event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system=Event.ElectoralSystem.PLURALITY,
        )
        self.ballot = Ballot.objects.create(event=self.event, voter_name="Becky")

    def test_ballot_submission(self):
        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": str(self.ballot.token)},
            json={"vote": "Ed's Fusion Chili"}
        )
        self.assertEqual(response.status_code, 200)

    def test_ballot_submission_with_bad_token(self):
        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": 'BAD_TOKEN'},
            json={"vote": "Ed's Fusion Chili", "token": "BAD_TOKEN"},
        )
        self.assertEqual(response.status_code, 403)
