"""
URL configuration for the account app.
Includes routes related to user profile management.
"""
from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('edit-profile/<int:pk>/', views.edit_profile, name='edit_profile'),
]