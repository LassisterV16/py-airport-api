from django.db import transaction
from rest_framework import serializers

from airport.models import (
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Crew,
    Flight,
    Order,
    Ticket,
)


class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("id", "name", "closest_big_city")


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ("id", "source", "destination", "distance")


class RouteListSerializer(RouteSerializer):
    source = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    destination = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )


class AirplaneTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AirplaneType
        fields = ("id", "name")


class AirplaneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airplane
        fields = (
            "id",
            "name",
            "rows",
            "seats_in_row",
            "airplane_type",
            "capacity"
        )


class AirplaneListSerializer(AirplaneSerializer):
    airplane_type = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )


class CrewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crew
        fields = ("id", "first_name", "last_name", "full_name")


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = (
            "id",
            "route",
            "airplane",
            "departure_time",
            "arrival_time",
            "crew"
        )


class FlightListSerializer(FlightSerializer):
    route = serializers.StringRelatedField()
    airplane = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    crew = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )


class FlightDetailSerializer(FlightListSerializer):
    route = RouteListSerializer()
    airplane = AirplaneListSerializer()


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "flight", "order")
        read_only_fields = ("order",)

    def validate(self, attrs):
        flight = attrs["flight"]
        row = attrs["row"]
        seat = attrs["seat"]

        if not 1 <= row <= flight.airplane.rows:
            raise serializers.ValidationError(
                {"row": f"Row number must be in range (1, {flight.airplane.rows})."}
            )

        if not 1 <= seat <= flight.airplane.seats_in_row:
            raise serializers.ValidationError(
                {"seat": f"Seat number must be in range (1, {flight.airplane.seats_in_row})."}
            )

        if Ticket.objects.filter(
            flight=flight,
            row=row,
            seat=seat
        ).exists():
            raise serializers.ValidationError("This seat is already reserved!")

        return attrs


class TicketListSerializer(TicketSerializer):
    flight = serializers.StringRelatedField()


class TicketDetailSerializer(TicketSerializer):
    flight = FlightDetailSerializer()


class OrderSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Order
        fields = ("id", "tickets", "created_at")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            order = Order.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(order=order, **ticket_data)
            return order


class OrderListSerializer(OrderSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)


class OrderDetailSerializer(OrderSerializer):
    tickets = TicketDetailSerializer(many=True, read_only=True)
