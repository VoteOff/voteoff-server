from django.test import TestCase
from ninja.testing import TestClient, TestAsyncClient
from .models import Event, Ballot
from .api import router


class EventTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)
        self.aclient = TestAsyncClient(router)
        self.event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system="PL",
        )

    async def test_create_event(self):
        response = await self.aclient.post(
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
        response = self.client.get(
            f"/event/{self.event.id}",
            query_params={"token": str(self.event.host_token)},
        )
        self.assertEqual(response.status_code, 200)

    def test_read_event_without_token(self):
        event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system="PL",
        )
        response = self.client.get(f"/event/{event.id}")
        self.assertEqual(response.status_code, 403)


class BallotTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)
        self.event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system="PL",
        )
        self.ballot = Ballot.objects.create(event=self.event, voter_name="Becky")

    def test_ballot_creation(self):
        response = self.client.post(
            f"/event/{self.event.id}/create-ballot",
            query_params={
                "voter_name": "Don",
                "share_token": str(self.event.share_token),
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_ballot_creation_with_duplicate_name(self):
        response = self.client.post(
            f"/event/{self.event.id}/create-ballot",
            query_params={
                "voter_name": "Becky",
                "share_token": str(self.event.share_token),
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_ballot_submission(self):
        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": str(self.ballot.token)},
            json={"vote": "Ed's Fusion Chili"},
        )
        self.assertEqual(response.status_code, 200)

    def test_ballot_resubmission(self):
        submission = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": str(self.ballot.token)},
            json={"vote": "Ed's Fusion Chili"},
        )
        self.assertEqual(submission.status_code, 200)

        resubmission = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": str(self.ballot.token)},
            json={"vote": "Tom's Texas Chili"},
        )
        self.assertEqual(resubmission.status_code, 403)

    def test_ballot_submission_with_bad_token(self):
        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": "BAD_TOKEN"},
            json={"vote": "Ed's Fusion Chili", "token": "BAD_TOKEN"},
        )
        self.assertEqual(response.status_code, 403)
