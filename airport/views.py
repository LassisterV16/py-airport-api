from datetime import datetime, time
from django.utils import timezone

from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

from airport.models import (
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Crew,
    Flight,
    Order,
)
from airport.serializers import (
    AirportSerializer,
    RouteSerializer,
    AirplaneTypeSerializer,
    AirplaneSerializer,
    CrewSerializer,
    FlightSerializer,
    OrderSerializer,
    RouteListSerializer,
    AirplaneListSerializer,
    FlightListSerializer,
    FlightDetailSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
)


class AirportViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer


class RouteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Route.objects.select_related("source", "destination")
    serializer_class = RouteSerializer

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return RouteListSerializer

        return RouteSerializer


class AirplaneTypeViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = AirplaneType.objects.all()
    serializer_class = AirplaneTypeSerializer


class AirplaneViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Airplane.objects.select_related("airplane_type")
    serializer_class = AirplaneSerializer

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return AirplaneListSerializer

        return AirplaneSerializer


class CrewViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class FlightViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        Flight.objects
        .select_related(
            "route__source",
            "route__destination",
            "airplane__airplane_type"
        )
        .prefetch_related("crew")
    )
    serializer_class = FlightSerializer

    @staticmethod
    def _params_to_ints(qs):
        return [int(str_id) for str_id in qs.split(",")]

    @staticmethod
    def _date_to_range(str_date):
        date = datetime.strptime(str_date, "%Y-%m-%d").date()
        return (
            timezone.make_aware(datetime.combine(date, time.min)),
            timezone.make_aware(datetime.combine(date, time.max))
        )

    def get_queryset(self):
        source = self.request.query_params.get("source")
        destination = self.request.query_params.get("destination")
        departure_time = self.request.query_params.get("departure-time")
        arrival_time = self.request.query_params.get("arrival-time")

        queryset = self.queryset

        if source:
            source_ids = self._params_to_ints(source)
            queryset = queryset.filter(route__source_id__in=source_ids)

        if destination:
            destination_ids = self._params_to_ints(destination)
            queryset = queryset.filter(route__destination_id__in=destination_ids)

        if departure_time:
            datetime_range = self._date_to_range(departure_time)
            queryset = queryset.filter(departure_time__range=datetime_range)

        if arrival_time:
            datetime_range = self._date_to_range(arrival_time)
            queryset = queryset.filter(arrival_time__range=datetime_range)

        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return FlightListSerializer

        if self.action == "retrieve":
            return FlightDetailSerializer

        return FlightSerializer


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Order.objects
            .filter(user=self.request.user)
            .prefetch_related(
                "tickets__flight__route__source",
                "tickets__flight__route__destination",
                "tickets__flight__airplane__airplane_type",
                "tickets__flight__crew"
            )
        )

    def get_serializer_class(self):
        if self.action == "list":
            return OrderListSerializer

        if self.action == "retrieve":
            return OrderDetailSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
