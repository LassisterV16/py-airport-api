from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from airport.models import Order, Ticket
from airport.serializers import OrderDetailSerializer
from airport.tests.utils import sample_flight

ORDER_URL = reverse("airport:order-list")


def detail_order_url(order_id):
    return reverse("airport:order-detail", args=[order_id])


class UnauthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_unauthenticated_order_list_forbidden(self):
        res = self.client.get(ORDER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_order_post_forbidden(self):
        res = self.client.post(ORDER_URL, {})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticatedOrderApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user", "password"
        )
        self.client.force_authenticate(self.user)
        self.flight = sample_flight()

    def test_authenticated_order_post_allowed(self):
        order_payload = {
            "tickets": [
                {
                    "row": 1,
                    "seat": 2,
                    "flight": self.flight.id,
                }
            ]
        }
        res = self.client.post(ORDER_URL, order_payload, format="json")
        order = Order.objects.get(id=res.data["id"])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order.user, self.user)

    def test_list_orders_shows_only_own_orders(self):
        other_user = get_user_model().objects.create_user(
            "other_user",
            "password"
        )
        order = Order.objects.create(user=self.user)
        Order.objects.create(user=other_user)
        res = self.client.get(ORDER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], order.id)

    def test_retrieve_own_order_detail_allowed(self):
        order = Order.objects.create(user=self.user)
        serializer = OrderDetailSerializer(order)
        url = detail_order_url(order.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_other_user_order_not_found(self):
        other_user = get_user_model().objects.create_user(
            "other_user",
            "password"
        )
        order = Order.objects.create(user=other_user)
        url = detail_order_url(order.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class OrderValidationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "username", "password"
        )
        self.client.force_authenticate(self.user)
        self.flight = sample_flight()

    def test_ticket_row_exceeds_airplane_capacity(self):
        payload = {
            "tickets": [
                {
                    "row": self.flight.airplane.rows + 1,
                    "seat": 1,
                    "flight": self.flight.id,
                }
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_ticket_seat_exceeds_airplane_capacity(self):
        payload = {
            "tickets": [
                {
                    "row": 1,
                    "seat": self.flight.airplane.seats_in_row + 1,
                    "flight": self.flight.id,
                }
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_ticket_seat_already_taken(self):
        other_user = get_user_model().objects.create_user(
            "other_user", "password"
        )
        other_user_order = Order.objects.create(user=other_user)
        Ticket.objects.create(
            row=1,
            seat=1,
            flight=self.flight,
            order=other_user_order,
        )
        payload = {
            "tickets": [
                {
                    "row": 1,
                    "seat": 1,
                    "flight": self.flight.id,
                }
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Ticket.objects.count(), 1)

    def test_duplicate_tickets_in_single_order(self):
        payload = {
            "tickets": [
                {
                    "row": 1,
                    "seat": 1,
                    "flight": self.flight.id,
                },
                {
                    "row": 1,
                    "seat": 1,
                    "flight": self.flight.id,
                }
            ]
        }
        res = self.client.post(ORDER_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Ticket.objects.count(), 0)
