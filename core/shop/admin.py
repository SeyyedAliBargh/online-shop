from django.contrib import admin
from shop.models import Product, Category, Comment, Rating, Image, ProductFeature


# ---------------------------------------------
# Inline admin class for ProductFeature model
# ---------------------------------------------
class FeaturesInline(admin.TabularInline):
    """
    Allows admin users to manage ProductFeature objects
    directly within the Product admin page.
    """
    model = ProductFeature
    extra = 0  # Number of empty forms displayed by default


# ---------------------------------------------
# Inline admin class for Product Images
# ---------------------------------------------
class ImageInline(admin.TabularInline):
    """
    Allows admin users to add and edit product images
    directly from the Product admin page.
    """
    model = Image
    extra = 0  # No extra empty form rows by default


# ---------------------------------------------
# Product Admin
# ---------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Product model.
    Includes inline editing for features and images.
    """
    list_display = ['name', 'original_price', 'created_at']  # Fields displayed in the admin list view
    inlines = [FeaturesInline, ImageInline]  # Add related features and images inline


# ---------------------------------------------
# Category Admin
# ---------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.
    """
    list_display = ['name', 'slug']  # Display category name and slug


# ---------------------------------------------
# Comment Admin
# ---------------------------------------------
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Comment model.
    """
    list_display = ['user']  # Display the user who wrote the comment


# ---------------------------------------------
# Rating Admin
# ---------------------------------------------
@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Rating model.
    Provides quick access to product, user, score, and timestamps.
    """
    list_display = ('product', 'user', 'score', 'created')
    search_fields = ('product__name', 'user__phone')  # Enables search by product name or user phone number
