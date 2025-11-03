from django.urls import path
from . import views


app_name = 'cart'

urlpatterns = [
    path('detail/', views.detail_cart, name='detail_cart'),
    path('add/',  views.add, name='add_cart'),
    path('update-quantity', views.update_quantity, name='update_quantity'),

    path('delete-product', views.delete_product, name='delete_product'),
]