from django.test import TestCase, Client
from ninja.testing import TestClient
from .models import Event, Ballot
from .api import router


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
            json={"vote": "Ed's Fusion Chili", "token": self.ballot.token},
        )
        self.assertEqual(response.status_code, 200)

    def test_ballot_submission_with_bad_token(self):
        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            json={"vote": "Ed's Fusion Chili", "token": "BAD_TOKEN"},
        )
        self.assertEqual(response.status_code, 403)

    def test_malformed_ballot_submission(self):

        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            json={
                "vote": [
                    "Tom's Texas Chili",
                    "Jim's Vegan Chili",
                    "Ed's Fusion Chili",
                ],  # Not formatted for plurality election
                "token": self.ballot.token,
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_ballot_submission_with_bad_choice(self):
        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            json={
                "vote": "Geoff's Christmas Chili",  # Not an offered choice
                "token": self.ballot.token,
            },
        )

        self.assertEqual(response.status_code, 422)


class RankedChoiceBallotTestCase(TestCase):

    def setUp(self):
        self.client = TestClient(router)
        self.event = Event.objects.create(
            name="Big Ranked Choice Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system=Event.ElectoralSystem.RANKED_CHOICE,
        )
        self.ballot = Ballot.objects.create(event=self.event, voter_name="Becky")

    def test_ballot_submission(self):

        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            json={
                "vote": ["Ed's Fusion Chili", "Tom's Texas Chili", "Jim's Vegan Chili"],
                "token": self.ballot.token,
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_malformed_ballot(self):

        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            json={
                "vote": "Ed's Fusion Chili",  # Not formatted for ranked choice election
                "token": self.ballot.token,
            },
        )
        self.assertEqual(response.status_code, 422)

    def test_ballot_with_bad_choice(self):
        response = self.client.post(
            f"/ballot/{self.ballot.id}/submit",
            json={
                "vote": [
                    "Geoff's Christmas Chili",  # Not an offered choice
                    "Tom's Texas Chili",
                    "Jim's Vegan Chili",
                ],
                "token": self.ballot.token,
            },
        )
        self.assertEqual(response.status_code, 422)
