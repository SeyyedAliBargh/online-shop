"""
URL configuration for the shop app.
"""
from django.urls import path
from . import views


app_name = "shop"

urlpatterns = [
    path("", views.index, name="index"),
    path("products/", views.products_list, name="products_list"),
    path("products/category/<slug:category_slug>/", views.products_list, name="products_by_category"),
    path("product/<slug:slug>/", views.product_detail, name="product_detail"),
    path("products/off/", views.products_list_discount, name="products_list_discount"),
    path("search/", views.search, name="search"),
    path('product/<slug:slug>/comment/', views.product_comments, name='product_comment'),
    path('product/<int:pk>/rate/', views.rate_product, name='rate_product'),
]