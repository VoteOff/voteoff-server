from datetime import datetime, UTC

from django.test import TestCase
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
        response = self.client.get(
            f"/event/{self.event.id}",
            query_params={"host_token": str(self.event.host_token)},
        )
        self.assertEqual(response.status_code, 200)

    def test_read_event_without_token(self):
        event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system=Event.ElectoralSystem.PLURALITY,
        )
        response = self.client.get(f"/event/{event.id}")
        self.assertEqual(response.status_code, 403)

    def test_get_ballot_statuses(self):
        Ballot.objects.create(
            event=self.event, voter_name="Ned", submitted=datetime.now(tz=UTC)
        )
        Ballot.objects.create(event=self.event, voter_name="Ted")

        response = self.client.get(
            f"/event/{self.event.id}/ballot-statuses",
            query_params={"host_token": str(self.event.host_token)},
        )

        self.assertEqual(response.data, {"pending": ["Ted"], "submitted": ["Ned"]})

    def test_get_ballot_results(self):
        votes = [
            ("Geoff", "Vote data"),
            ("Lance", ["Could", "be", "any", "format"]),
            ("Paul", {"We": 10, "don't": 5, "care": 0}),
        ]
        vote_data = [v[1] for v in votes]

        for name, data in votes:
            Ballot.objects.create(event=self.event, voter_name=name, vote=data)

        response = self.client.get(
            f"/event/{self.event.id}/ballot-results",
            query_params={"host_token": str(self.event.host_token)},
        )

        self.assertListEqual(vote_data, response.data)


class BallotTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)
        self.event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system=Event.ElectoralSystem.PLURALITY,
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
        print(resubmission.status_code, resubmission.data)
        self.assertEqual(resubmission.status_code, 403)

    def test_ballot_submission_with_bad_token(self):
        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": "BAD_TOKEN"},
            json={"vote": "Ed's Fusion Chili", "token": "BAD_TOKEN"},
        )
        self.assertEqual(response.status_code, 403)
