from django.contrib import admin
from .models import Bus, Seat, Booking


class BusAdmin(admin.ModelAdmin):
    # Controls how Bus objects are displayed in Django admin list view.
    # `list_display` is a tuple of model field names (or callables) shown as columns.
    list_display = ('bus_name', 'number', 'origin', 'destination', 'start_time', 'reach_time', 'no_of_seats', 'price')

class SeatAdmin(admin.ModelAdmin):
    # Controls how Seat objects are displayed in admin; shows seat number, linked bus, and booking status.
    list_display = ('seat_number', 'bus', 'is_booked')

class BookingAdmin(admin.ModelAdmin):
    # Controls Booking admin list view to show which user booked which seat on which bus, plus time and price.
    list_display = ('user', 'bus', 'seat', 'booking_time', 'origin','price')

# Register the models with the Django admin site so they can be managed via the admin UI.
admin.site.register(Bus, BusAdmin)
admin.site.register(Seat, SeatAdmin)
admin.site.register(Booking, BookingAdmin)
