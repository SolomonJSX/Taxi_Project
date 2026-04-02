from django.contrib import admin
from .models import Car, Driver, Order, Tariff

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'plate_number', 'car_class', 'driver', 'status')
    list_editable = ('status', 'driver') # Это позволит менять водителя прямо из списка!

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'iin', 'experience')

admin.site.register(Order)
admin.site.register(Tariff)
# ЗДЕСЬ НЕ ДОЛЖНО БЫТЬ CustomUser или User!