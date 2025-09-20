Bookings app — documentation

Overview
The `bookings` Django app implements a simple bus booking system. It includes models for `Bus`, `Seat`, and `Booking`, serializers for API input/output, views for registering/logging in users and creating/listing buses and bookings, and a signals handler to auto-create seats when a bus is created.

Files and responsibilities

- `models.py`
  - Bus: stores bus details (name, unique number, origin, destination, features, start/reach time, number of seats, price).
  - Seat: represents a seat for a specific bus, tracks seat number and whether it's booked.
  - Booking: links a user to a bus and seat and stores booking time. Provides convenience properties `price`, `origin`, `destination` that proxy the linked bus.

- `serializers.py`
  - `UserRegisterSerializer`: used to create new users. Accepts username, email, and password (write-only). `create` method uses `create_user` to hash password.
  - `SeatSerializer`: serializes seat id, number and booking status.
  - `BusSerializer`: serializes bus fields and nested `seats` list (read-only).
  - `BusSummarySerializer`: small summary with bus name, number, origin, destination used in booking responses.
  - `BookingSerializer`: read-only fields for `user`, `booking_time`, `bus`, `seat`, `price`, `origin`, `destination` and uses nested serializers for bus and seat in responses.

- `views.py`
  - `RegisterView` (APIView.post): registers a new user, returns an auth token on success.
    Expected input JSON: {"username":"...","email":"...","password":"..."}
    Expected response (201): {"token":"<token>"}

  - `LoginView` (APIView.post): authenticates credentials and returns token and user_id.
    Expected input JSON: {"username":"...","password":"..."}
    Expected response (200): {"token":"<token>", "user_id": <id>}
    Error (401) on invalid credentials: {"error":"Invalid Credentials"}

  - `BusListCreateView` (ListCreateAPIView): GET lists buses, POST creates a bus.
    POST payload: all Bus fields (e.g. bus_name, number, origin, destination, features, start_time, reach_time, no_of_seats, price)
    On bus creation the `post_save` signal creates seats automatically.

  - `BusDetailView` (RetrieveUpdateDestroyAPIView): GET/PUT/DELETE on a single bus resource.

  - `BookingView` (APIView.post, IsAuthenticated): creates a booking for a seat.
    Expected input JSON: {"seat": <seat_id>} with an Authorization header `Token <token>`.
    Behavior: checks seat exists/unbooked, marks seat as booked, creates Booking linked to request.user and the seat's bus, and returns serialized booking (201) or error (400).

  - `UserBookingView` (APIView.get, IsAuthenticated): lists bookings for a user.
    URL: `/user/<user_id>/bookings/` with auth token. Returns 401 if the requesting user id doesn't match the URL user_id.

- `urls.py`
  - Routes for buses, register, login, user bookings, and booking creation.

- `signals.py`
  - `create_seats_for_bus`: when a Bus is created, creates Seat objects numbered S1..SN where N is `no_of_seats`.

Example request/response flow
1) Create a bus (POST /buses/) with `no_of_seats: 5` -> signal creates 5 Seat rows with seat_number S1..S5.
2) Register user (POST /register/) -> returns token.
3) Login user (POST /login/) -> returns token.
4) Make booking (POST /booking/ with {"seat": <seat_id>} and Authorization header) -> returns booking object, seat is flagged booked.

Notes and edge cases
- Concurrency: two users could try to book the same seat simultaneously; this code does a read-check and save but doesn't lock or use transactions - consider adding select_for_update inside a transaction to avoid race conditions.
- OneDrive: if the project lives on OneDrive, file-change monitoring may be slower; use `--noreload` for runserver while debugging.
- The `UserRegisterSerializer.create` parameter is named `validate_date` (typo) - consider renaming to `validated_data` for clarity.

Next steps (optional)
- Add unit tests for booking flow and seat creation.
- Add optimistic locking or DB transactions to prevent double-booking.
- Add pagination for bus list if many buses expected.

