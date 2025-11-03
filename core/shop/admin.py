from django.contrib import admin

from order.models import Order
from shop.models import *
# Register your models here.


class FeaturesInline(admin.TabularInline):
    model = ProductFeature
    extra = 0


class ImageInline(admin.TabularInline):
    model = Image
    extra = 0


# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'original_price', 'created_at' ]
    inlines = [FeaturesInline, ImageInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user']

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'score', 'created')
    search_fields = ('product__name', 'user__phone')