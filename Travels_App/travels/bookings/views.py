
# Views for the bookings app with explanations of "what" and "why".
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status, generics
from rest_framework.views import APIView
from .serializers import UserRegisterSerializer, BusSerializer, BookingSerializer
from rest_framework.response import Response
from .models import Bus, Seat, Booking


class RegisterView(APIView):
        """Registers a new user and returns an auth token.

        Why use Token here?
        - The project uses DRF's token authentication for simplicity. Returning a
            token immediately after registration saves the caller an extra login
            step.
        """

        def post(self, request):
                serializer = UserRegisterSerializer(data=request.data)
                if serializer.is_valid():
                        user = serializer.save()
                        # Create or reuse a token for the new user; tokens are persistent
                        # until explicitly deleted which is convenient for client apps.
                        token, created = Token.objects.get_or_create(user=user)
                        return Response({'token': token.key}, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
        """Authenticates credentials and returns an auth token + user id.

        Why not return the full user object?
        - For security and simplicity we return only the token and user id; the
            client can fetch profile information using other endpoints if needed.
        """

        def post(self, request):
                username = request.data.get('username')
                password = request.data.get('password')
                user = authenticate(username=username, password=password)

                if user:
                        token, created = Token.objects.get_or_create(user=user)
                        return Response({
                                'token': token.key,
                                'user_id': user.id
                        }, status=status.HTTP_200_OK)
                else:
                        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class BusListCreateView(generics.ListCreateAPIView):
        """Lists buses and allows creation of a Bus.

        Why ListCreateAPIView?
        - The generic view handles GET list and POST create with minimal code and
            built-in pagination support if enabled globally.
        """

        queryset = Bus.objects.all()
        serializer_class = BusSerializer


class BusDetailView(generics.RetrieveUpdateDestroyAPIView):
        """Retrieve, update or delete a single Bus instance.

        Using the generic view gives us standard behavior and HTTP status codes
        without custom code.
        """

        queryset = Bus.objects.all()
        serializer_class = BusSerializer


class BookingView(APIView):
        """Create a booking for a seat.

        Flow and rationale:
        - The endpoint expects a `seat` id. We check if the seat exists and is
            not already booked. We then mark it booked and create a Booking record.
        - We keep this logic explicit instead of relying on serializers here so we
            can perform the seat check and atomic update easily.
        - Note: This implementation is vulnerable to race conditions if two
            requests try to book the same seat at the same time; for production
            safety use a DB transaction with `select_for_update`.
        """

        permission_classes = [IsAuthenticated]

        def post(self, request):
                seat_id = request.data.get('seat')
                try:
                        seat = Seat.objects.get(id=seat_id)
                        if seat.is_booked:
                                return Response({'error': 'Seat already booked'}, status=status.HTTP_400_BAD_REQUEST)

                        # Mark seat as booked and persist. We do this before creating the
                        # Booking to reduce the window where another request could claim
                        # the seat (still not fully safe without DB locking).
                        seat.is_booked = True
                        seat.save()

                        bookings = Booking.objects.create(
                                user=request.user,
                                bus=seat.bus,
                                seat=seat
                        )
                        serializer = BookingSerializer(bookings)
                        return Response(serializer.data, status=status.HTTP_201_CREATED)
                except Seat.DoesNotExist:
                        return Response({'error': 'Invalid Seat ID'}, status=status.HTTP_400_BAD_REQUEST)


class UserBookingView(APIView):
        """Returns bookings for a user.

        Why require user_id in the URL?
        - The API is explicit about which user's bookings are being requested.
        - We also verify that the requesting user matches the URL user_id to
            prevent users from listing other users' bookings.
        """

        permission_classes = [IsAuthenticated]

        def get(self, request, user_id):
                if request.user.id != user_id:
                        return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

                bookings = Booking.objects.filter(user_id=user_id)
                serializer = BookingSerializer(bookings, many=True)
                return Response(serializer.data)
