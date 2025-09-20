
from rest_framework import serializers
from .models import Bus, Seat, Booking
from django.contrib.auth.models import User


# Serializer used to register new users.
# Password is write-only so it won't be returned in API responses.
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        """Create a new Django user using create_user to ensure the
        password is hashed.

        Args:
            validated_data (dict): validated data from the serializer

        Returns:
            User: newly created Django user

        Expected input JSON example:
        {
            "username": "alice",
            "email": "alice@example.com",
            "password": "s3cret"
        }

        Expected output: a User instance is created and returned by the serializer
        (the view typically returns an auth token, not the user object).
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


# Simple serializer for Seat model: id, seat_number and booking status.
class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ['id', 'seat_number', 'is_booked']


# Serializer for Bus model. Includes nested seats (read-only) so bus list/detail
# responses include the seat records that were created by the post_save signal.
class BusSerializer(serializers.ModelSerializer):
    seats = SeatSerializer(many=True, read_only=True)

    class Meta:
        model = Bus
        fields = '__all__'


# Lightweight bus representation used inside Booking responses to avoid
# repeating all bus fields.
class BusSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = ['bus_name', 'number', 'origin', 'destination']


# BookingSerializer returns booking details. Several fields are read-only
# because bookings are created server-side (user, booking_time, bus, seat,
# and derived properties like price/origin/destination).
class BookingSerializer(serializers.ModelSerializer):
    bus = BusSummarySerializer(read_only=True)
    seat = SeatSerializer(read_only=True)
    user = serializers.StringRelatedField()
    price = serializers.StringRelatedField()
    origin = serializers.StringRelatedField()
    destination = serializers.StringRelatedField()

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['user', 'booking_time', 'bus', 'seat', 'price', 'origin', 'destination']
