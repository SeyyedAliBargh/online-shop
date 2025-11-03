from django.urls import path
from . import views
app_name = "order"
urlpatterns = [
    path("order-detail/<int:order_id>", views.order_detail, name="order_detail"),
    path("verify-phone/", views.verify_phone, name="verify_phone"),
    path("verify-code/", views.verify_code, name="verify_code"),
    path("order-create/", views.order_create, name="order_create"),
    path("verify/", views.verify, name="verify"),
    path("request/", views.send_request, name="request"),
]