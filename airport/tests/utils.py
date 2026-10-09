from airport.models import (
    Airport,
    Route,
    AirplaneType,
    Airplane,
    Flight,
)


def sample_flight(**params):
    source = Airport.objects.create(name="AMS", closest_big_city="Amsterdam")
    destination = Airport.objects.create(name="MUC", closest_big_city="Munich")
    route = Route.objects.create(
        source=source, destination=destination, distance=665
    )

    airplane_type = AirplaneType.objects.create(name="Narrow-body airliner")
    airplane = Airplane.objects.create(
        name="Boeing 737",
        rows=33,
        seats_in_row=6,
        airplane_type=airplane_type
    )

    defaults = {
        "route": route,
        "airplane": airplane,
        "departure_time": "2026-10-01T10:00:00Z",
        "arrival_time": "2026-10-01T13:00:00Z",
    }
    defaults.update(params)

    return Flight.objects.create(**defaults)
