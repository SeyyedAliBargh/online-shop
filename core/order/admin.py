from .models import Order, OrderItem
from django.contrib import admin
# Register your models here.


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    raw_id_fields = ["product"]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "buyer","first_name", "last_name", "phone", "postal_code", "province", "city",
                    "paid", "created", "updated", "updated"]
    list_filter = ["paid", "updated", "created"]
    inlines = [OrderItemInline]