import uuid
from django.test import TestCase
from ninja.testing import TestAsyncClient
from ..models import Event, Ballot
from ..api import router


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

    async def test_get_event_with_host_token(self):
        response = await self.aclient.get(
            f"/event/{self.event.id}",
            headers={"X-API-Key": self.event.host_token},
        )
        self.assertEqual(response.status_code, 200)

    async def test_get_event_with_share_token(self):
        response = await self.aclient.get(
            f"/event/{self.event.id}",
            headers={"X-API-Key": self.event.share_token},
        )
        self.assertEqual(response.status_code, 200)

    async def test_get_event_with_ballot_token(self):
        ballot = await Ballot.objects.acreate(event=self.event, voter_name="Becky")

        response = await self.aclient.get(
            f"/event/{self.event.id}",
            headers={"X-API-Key": ballot.token},
        )
        self.assertEqual(response.status_code, 200)

    async def test_get_event_with_random_token(self):
        response = await self.aclient.get(
            f"/event/{self.event.id}", headers={"X-API-Key": uuid.uuid4()}
        )
        self.assertEqual(response.status_code, 403)

    async def test_get_event_with_no_token(self):
        response = await self.aclient.get(f"/event/{self.event.id}")
        self.assertEqual(response.status_code, 422)

    async def test_get_event_with_ballot_token_from_different_event(self):
        another_event = await Event.objects.acreate(
            name="Small Cookoff",
            choices=["Sally's Salsa", "Bob's Guacamole"],
            electoral_system="PL",
        )
        ballot = await Ballot.objects.acreate(event=another_event, voter_name="Becky")

        response = await self.aclient.get(
            f"/event/{self.event.id}",
            headers={"X-API-Key": ballot.token},
        )
        self.assertEqual(response.status_code, 403)

    async def test_get_event_with_invalid_token(self):
        response = await self.aclient.get(
            f"/event/{self.event.id}", headers={"X-API-Key": "not-a-uuid"}
        )
        self.assertEqual(response.status_code, 422)

    async def test_patch_event(self):
        response = await self.aclient.patch(
            f"/event/{self.event.id}",
            json={
                "allow_registration": True,
                "allow_voting": True,
                "show_results": True,
            },
            headers={"X-API-Key": self.event.host_token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["allow_registration"], True)
        self.assertEqual(response.json()["allow_voting"], True)
        self.assertEqual(response.json()["show_results"], True)

    async def test_patch_event_with_partial_updates(self):
        response = await self.aclient.patch(
            f"/event/{self.event.id}",
            json={"allow_registration": True},
            headers={"X-API-Key": self.event.host_token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["allow_registration"], True)
        self.assertEqual(response.json()["allow_voting"], False)
        self.assertEqual(response.json()["show_results"], False)

    async def test_patch_event_with_random_token(self):
        response = await self.aclient.patch(
            f"/event/{self.event.id}",
            json={"allow_registration": True, "allow_voting": True},
            headers={"X-API-Key": uuid.uuid4()},
        )
        self.assertEqual(response.status_code, 403)
        await self.event.arefresh_from_db()
        self.assertEqual(self.event.allow_registration, False)
        self.assertEqual(self.event.allow_voting, False)

    async def test_close_event(self):
        self.event.allow_registration = True
        self.event.allow_registration = True
        await self.event.asave()

        response = await self.aclient.post(
            f"/event/{self.event.id}/close",
            headers={"X-API-Key": self.event.host_token},
        )
        self.assertEqual(response.status_code, 200)

        event = await Event.objects.aget(pk=self.event.id)

        self.assertIsNotNone(event.closed)
        self.assertFalse(event.allow_registration)
        self.assertFalse(event.allow_voting)

    async def test_close_event_with_random_token(self):
        self.event.allow_registration = True
        self.event.allow_voting = True
        await self.event.asave()

        response = await self.aclient.post(
            f"/event/{self.event.id}/close",
            headers={"X-API-Key": uuid.uuid4()},
        )
        self.assertEqual(response.status_code, 403)

        event = await Event.objects.aget(pk=self.event.id)

        self.assertIsNone(event.closed)
        self.assertTrue(event.allow_registration)
        self.assertTrue(event.allow_voting)
