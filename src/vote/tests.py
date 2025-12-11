from datetime import datetime, timezone
import uuid
from django.test import TestCase
from ninja.testing import TestClient, TestAsyncClient
from .models import Event, Ballot
from .api import router


class EventTestCase(TestCase):
    def setUp(self):
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

    async def test_read_event(self):
        response = await self.aclient.get(
            f"/event/{self.event.id}",
            query_params={"token": str(self.event.host_token)},
        )
        self.assertEqual(response.status_code, 200)

    async def test_read_event_without_token(self):
        event = Event(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system="PL",
        )
        await event.asave()
        response = await self.aclient.get(f"/event/{event.id}")
        self.assertEqual(response.status_code, 403)

    async def test_close_event(self):
        response = await self.aclient.post(
            f"/event/{self.event.id}/close",
            query_params={"host_token": str(self.event.host_token)},
        )
        self.assertEqual(response.status_code, 200)

        event = await Event.objects.aget(pk=self.event.id)

        self.assertIsNotNone(event.closed)

    async def test_open_event(self):
        self.event.closed = datetime.now(timezone.utc)
        await self.event.asave()

        response = await self.aclient.post(
            f"/event/{self.event.id}/open",
            query_params={"host_token": str(self.event.host_token)},
        )
        self.assertEqual(response.status_code, 200)

        event = await Event.objects.aget(pk=self.event.id)

        self.assertIsNone(event.closed)


class BallotTestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)
        self.aclient = TestAsyncClient(router)
        self.event = Event.objects.create(
            name="Big Cookoff",
            choices=["Tom's Texas Chili", "Jim's Vegan Chili", "Ed's Fusion Chili"],
            electoral_system="PL",
        )
        self.ballot = Ballot.objects.create(event=self.event, voter_name="Becky")

    async def test_ballot_creation(self):
        response = await self.aclient.post(
            f"/event/{self.event.id}/create-ballot",
            query_params={
                "voter_name": "Don",
                "share_token": self.event.share_token,
            },
        )

        self.assertEqual(response.status_code, 200)

    async def test_ballot_creation_with_duplicate_name(self):
        response = await self.aclient.post(
            f"/event/{self.event.id}/create-ballot",
            query_params={
                "voter_name": "Becky",
                "share_token": self.event.share_token,
            },
        )
        self.assertEqual(response.status_code, 422)

    async def test_ballot_creation_with_bad_token(self):
        response = await self.aclient.post(
            f"/event/{self.event.id}/create-ballot",
            query_params={
                "voter_name": "Don",
                "share_token": uuid.uuid4(),
            },
        )
        self.assertEqual(response.status_code, 403)

    async def test_ballot_submission(self):
        response = await self.aclient.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": self.ballot.token},
            json={"vote": "Ed's Fusion Chili"},
        )
        self.assertEqual(response.status_code, 200)

    async def test_ballot_resubmission(self):
        submission = await self.aclient.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": self.ballot.token},
            json={"vote": "Ed's Fusion Chili"},
        )
        self.assertEqual(submission.status_code, 200)

        resubmission = await self.aclient.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": str(self.ballot.token)},
            json={"vote": "Tom's Texas Chili"},
        )
        self.assertEqual(resubmission.status_code, 403)

    async def test_ballot_submission_with_bad_token(self):
        response = await self.aclient.post(
            f"/ballot/{self.ballot.id}/submit",
            query_params={"token": uuid.uuid4()},
            json={"vote": "Ed's Fusion Chili"},
        )
        self.assertEqual(response.status_code, 403)

    async def test_ballot_list(self):
        event = Event(
            name="Small Cookoff",
            choices=["Chilli 1", "Chilli 2", "Chilli 3"],
            electoral_system="PL",
        )
        await event.asave()
        ballot1 = Ballot(event=event, voter_name="Bob")
        ballot2 = Ballot(event=event, voter_name="Jeff")
        ballot3 = Ballot(event=event, voter_name="Billy")
        await ballot1.asave()
        await ballot2.asave()
        await ballot3.asave()

        response = await self.aclient.get(
            f"/event/{event.id}/ballots",
            query_params={"token": event.host_token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

        response = await self.aclient.get(
            f"/event/{event.id}/ballots",
            query_params={"token": ballot1.token},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)

    async def test_ballot_list_unauthorized(self):
        event = Event(
            name="Small Cookoff",
            choices=["Chilli 1", "Chilli 2", "Chilli 3"],
            electoral_system="PL",
        )
        await event.asave()
        event1 = Event(
            name="Big Cooky",
            choices=["Chilli 1", "Chilli 2", "Chilli 3"],
            electoral_system="PL",
        )
        await event1.asave()

        ballot = Ballot(event=event, voter_name="Train")

        ballot1 = Ballot(event=event, voter_name="Bob")
        ballot2 = Ballot(event=event, voter_name="Jeff")
        ballot3 = Ballot(event=event, voter_name="Billy")
        await ballot1.asave()
        await ballot2.asave()
        await ballot3.asave()

        response = await self.aclient.get(
            f"/event/{event.id}/ballots",
            query_params={"token": event1.host_token},
        )

        self.assertEqual(response.status_code, 403)

        response = await self.aclient.get(
            f"/event/{event.id}/ballots",
            query_params={"token": ballot.token},
        )

        self.assertEqual(response.status_code, 403)

    async def test_get_ballot(self):
        response = await self.aclient.get(
            f"/ballot/{self.ballot.id}",
            query_params={"token": self.ballot.token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["voter_name"], "Becky")

    async def test_get_ballot_unauthorized(self):
        response = await self.aclient.get(
            f"/ballot/{self.ballot.id}",
            query_params={"token": uuid.uuid4()},
        )
        self.assertEqual(response.status_code, 403)
