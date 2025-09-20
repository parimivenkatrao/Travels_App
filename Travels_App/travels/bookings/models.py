from django.db import models
from django.contrib.auth.models import User

# Models for the bookings app.
# Each model includes a short comment explaining why the field exists and
# design choices (for future maintainers).


class Bus(models.Model):
        """Represents a bus service/trip.

        Why these fields?
        - `number` is unique so we can identify a specific vehicle or trip by a
            stable reference (helps in admin and in ticketing).
        - `features` is a free-text field to list things like 'AC, WiFi' — kept as
            TextField to allow variable length descriptions.
        - `no_of_seats` is a PositiveBigIntegerField because seat counts may be
            moderately large and must be non-negative.
        - `price` uses DecimalField to avoid floating-point rounding errors with
            money values.
        """

        bus_name = models.CharField(max_length=100)
        number = models.CharField(max_length=20, unique=True)  # unique ID for the bus/trip
        origin = models.CharField(max_length=50)               # starting location
        destination = models.CharField(max_length=50)          # end location
        features = models.TextField()                          # free-text feature list
        start_time = models.TimeField()                        # departure time
        reach_time = models.TimeField()                        # arrival time
        no_of_seats = models.PositiveBigIntegerField()         # used by signal to create Seat rows
        price = models.DecimalField(max_digits=8, decimal_places=2)  # currency amount

        def __str__(self):
                # Friendly admin/listing representation. We intentionally keep it
                # concise (name + number) to avoid very long strings in lists.
                return f"{self.bus_name} {self.number} "


class Seat(models.Model):
        """Represents a seat on a Bus.

        Why the design?
        - Seats are linked to a Bus via ForeignKey and use `related_name='seats'`
            so `bus.seats.all()` is convenient in serializers/views.
        - `is_booked` is a boolean that represents whether the seat is currently
            allocated; we update this when a Booking is created.
        """

        bus = models.ForeignKey('Bus', on_delete=models.CASCADE, related_name='seats')
        seat_number = models.CharField(max_length=10)  # e.g. 'S1', 'S2' — kept string to allow flexible labels
        is_booked = models.BooleanField(default=False)

        def __str__(self):
                # Keep the seat representation short for admin and logs.
                return f"{self.seat_number}"


class Booking(models.Model):
        """Links a user to a seat and bus at a point in time.

        Rationale and behavior notes:
        - `booking_time` uses `auto_now_add` because the creation timestamp is an
            immutable record of when the booking occurred.
        - We expose `price`, `origin`, and `destination` as properties that
            delegate to the related Bus. This avoids duplicating bus data in the
            booking table while keeping serializer access simple.
        - We intentionally do not denormalize price into Booking here to keep a
            single source of truth (the Bus). If prices can change and historical
            accuracy is required, store price at booking time instead.
        """

        user = models.ForeignKey(User, on_delete=models.CASCADE)
        bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
        seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
        booking_time = models.DateTimeField(auto_now_add=True)

        def __str__(self):
                return f"{self.user.username}-{self.bus.bus_name}-{self.bus.start_time}-{self.bus.reach_time}-{self.seat.seat_number}"

        @property
        def price(self):
                # Delegates to Bus.price — keeps Booking lightweight; change this
                # behavior if you need to snapshot the price at booking time.
                return self.bus.price

        @property
        def origin(self):
                return self.bus.origin

        @property
        def destination(self):
                return self.bus.destination
