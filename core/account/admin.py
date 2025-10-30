from django.contrib import admin
from .models import ShopUser, Profile
from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from .forms import ShopUserChangeForm, ShopUserCreationForm


# Register your models here.

@admin.register(ShopUser)
class UserAdmin(UserAdmin):
    """
    show User model in admin panel and customize it
    """
    ordering = ('phone',)
    add_form= ShopUserCreationForm
    form = ShopUserChangeForm
    model = ShopUser
    readonly_fields = ('date_joined', 'last_login')
    list_display = [ "email", "phone", "is_staff", "is_active"]
    search_fields = ('email', 'phone')

    fieldsets = (
        ("اطلاعات ضروری", {"fields": ("email", "phone", 'password')}),
        ("دسترسی های کاربر", {"fields": ("is_active", 'is_staff', 'is_superuser', 'user_permissions')}),
        ("تاریخ های مهم", {"fields": ("date_joined", 'last_login')}),

    )

    add_fieldsets = (
        ("اطلاعات ضروری", {"fields": ("email", "phone", "password1", "password2")}),
        ("دسترسی‌های کاربر", {"fields": ("is_active", "is_staff", "is_superuser", "user_permissions")}),
    )





@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    show the Profile model in admin panel
    """
    list_display = ('user', 'last_name', 'first_name', 'birth_date')