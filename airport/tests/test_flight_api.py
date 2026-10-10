from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from airport.models import (
    Route,
    Airport,
    Flight,
    Crew,
)
from airport.serializers import FlightDetailSerializer, FlightSerializer
from airport.tests.utils import sample_flight

FLIGHT_URL = reverse("airport:flight-list")


def detail_url(flight_id):
    return reverse("airport:flight-detail", args=[flight_id])


class UnauthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.flight = sample_flight()

    def test_flight_list_allowed(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_flight_detail_allowed(self):
        url = detail_url(self.flight.id)
        res = self.client.get(url)
        serializer = FlightDetailSerializer(self.flight)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_flight_put_forbidden(self):
        url = detail_url(self.flight.id)
        res = self.client.put(url, {})

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_flight_patch_forbidden(self):
        url = detail_url(self.flight.id)
        res = self.client.patch(url, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_flight_post_forbidden(self):
        res = self.client.post(FLIGHT_URL, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user",
            "password"
        )
        self.client.force_authenticate(self.user)
        self.flight = sample_flight()

    def test_flight_list_allowed(self):
        res = self.client.get(FLIGHT_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_flight_detail_allowed(self):
        url = detail_url(self.flight.id)
        res = self.client.get(url)
        serializer = FlightDetailSerializer(self.flight)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_flight_put_forbidden(self):
        url = detail_url(self.flight.id)
        res = self.client.put(url, {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_patch_forbidden(self):
        url = detail_url(self.flight.id)
        res = self.client.patch(url, {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_flight_post_forbidden(self):
        res = self.client.post(FLIGHT_URL, {})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class AdminFlightApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            "admin", "password", is_staff=True
        )
        self.client.force_authenticate(self.user)
        self.flight = sample_flight()

    def test_flight_post_allowed(self):
        crew = Crew.objects.create(first_name="John", last_name="Doe")
        payload = {
            "route": self.flight.route_id,
            "airplane": self.flight.airplane_id,
            "departure_time": "2027-01-01T10:00:00Z",
            "arrival_time": "2027-01-01T13:00:00Z",
            "crew": [crew.id]
        }
        res = self.client.post(FLIGHT_URL, payload, format="json")
        flight = Flight.objects.get(id=res.data["id"])
        serializer = FlightSerializer(flight)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Flight.objects.count(), 2)
        self.assertEqual(res.data, serializer.data)

    def test_flight_put_allowed(self):
        crew = Crew.objects.create(first_name="Brad", last_name="Pitt")
        payload = {
            "id": self.flight.id,
            "route": self.flight.route_id,
            "airplane": self.flight.airplane_id,
            "departure_time": "2026-10-01T12:00:00Z",
            "arrival_time": "2026-10-01T15:00:00Z",
            "crew": [crew.id]
        }
        url = detail_url(self.flight.id)
        res = self.client.put(url, payload, format="json")
        flight = Flight.objects.get(id=res.data["id"])
        serializer = FlightSerializer(flight)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_flight_patch_allowed(self):
        payload = {
            "arrival_time": "2026-10-01T17:00:00Z",
        }
        url = detail_url(self.flight.id)
        res = self.client.patch(url, payload, format="json")
        flight = Flight.objects.get(id=res.data["id"])
        serializer = FlightSerializer(flight)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


class FlightFilteringApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.airport_1 = Airport.objects.create(
            name="CDG", closest_big_city="Paris"
        )
        self.airport_2 = Airport.objects.create(
            name="LON", closest_big_city="London"
        )
        self.route_2 = Route.objects.create(
            source=self.airport_1, destination=self.airport_2, distance=450
        )
        self.route_3 = Route.objects.create(
            source=self.airport_2, destination=self.airport_1, distance=450
        )
        self.flight_1 = sample_flight()
        self.flight_2 = sample_flight(
            route=self.route_2,
            departure_time="2026-11-01T10:00:00Z",
            arrival_time="2026-11-01T13:00:00Z",
        )
        self.flight_3 = sample_flight(
            route=self.route_3,
            departure_time="2026-12-01T10:00:00Z",
            arrival_time="2026-12-01T13:00:00Z",
        )

    def test_filter_flights_by_source(self):
        res = self.client.get(FLIGHT_URL, {"source": f"{self.airport_1.id}"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], self.flight_2.id)

    def test_filter_flights_by_destination(self):
        res = self.client.get(
            FLIGHT_URL, {"destination": f"{self.airport_2.id}"}
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], self.flight_2.id)

    def test_filter_flights_by_departure_date(self):
        res = self.client.get(FLIGHT_URL, {"departure-time": "2026-11-01"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], self.flight_2.id)

    def test_filter_flights_by_arrival_date(self):
        res = self.client.get(FLIGHT_URL, {"arrival-time": "2026-11-01"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], self.flight_2.id)

    def test_filter_flights_by_source_and_departure_date(self):
        flight_4 = sample_flight(
            route=self.route_2,
            departure_time="2026-12-01T10:00:00Z",
            arrival_time="2026-12-01T13:00:00Z",
        )
        res = self.client.get(
            FLIGHT_URL,
            {
                "source": f"{self.airport_1.id}",
                "departure-time": "2026-12-01"
            }
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], flight_4.id)
