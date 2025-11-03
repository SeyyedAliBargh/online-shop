import os
from PIL import Image as PilImage
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg, Count
from django.urls import reverse
from django_jalali.db import models as jmodels
from django.utils.text import slugify
from django_resized import ResizedImageField
from account.models import ShopUser


class Category(models.Model):
    """
    Category model for classifying products.
    """
    name = models.CharField(max_length=100, verbose_name='name')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='slug')
    created = models.DateTimeField(auto_now_add=True, verbose_name='created at')

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Product model containing basic product info, pricing, discount logic,
    and rating aggregation.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name='category')
    inventory = models.PositiveIntegerField(default=0, verbose_name='inventory')
    name = models.CharField(max_length=100, verbose_name='name')
    description = models.TextField(verbose_name='description')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='slug')
    weight = models.PositiveIntegerField(default=0, verbose_name='weight (grams)')
    brand = models.CharField(max_length=250, blank=True, null=True, verbose_name='brand')
    original_price = models.PositiveIntegerField(default=0, verbose_name='original price')
    discount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percent must be between 0 and 100.",
        null=True,
        blank=True,
        verbose_name='discount (%)'
    )
    discounted_price = models.PositiveIntegerField(default=0, verbose_name='price after discount', null=True, blank=True)
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='created at')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='updated at')
    views = models.PositiveIntegerField(default=0, verbose_name='views')
    sold_count = models.PositiveIntegerField(default=0, verbose_name='sold count')

    # product rating
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, verbose_name='average rating')
    rating_count = models.PositiveIntegerField(default=0, verbose_name='rating count')

    class Meta:
        ordering = ('name', 'created_at')
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'product'
        verbose_name_plural = 'products'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """
        Returns the absolute URL for the product.
        """
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """
        Automatically generates a slug and calculates discounted price before saving.
        """
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        if self.discount:
            self.discounted_price = int(self.original_price * (100 - self.discount) / 100)
        else:
            self.discounted_price = self.original_price
        super().save(*args, **kwargs)

    def update_rating(self):
        """
        Updates product's average rating and count based on related ratings.
        """
        agg = self.ratings.aggregate(avg=Avg('score'), count=Count('id'))
        self.average_rating = agg['avg'] or 0
        self.rating_count = agg['count'] or 0
        self.save(update_fields=['average_rating', 'rating_count'])


class ProductFeature(models.Model):
    """
    Each product can have one or many features (key-value attributes).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features', verbose_name='product')
    name = models.CharField(max_length=100, verbose_name='feature name')
    value = models.CharField(max_length=250, verbose_name='feature value')

    class Meta:
        ordering = ('name',)
        indexes = [models.Index(fields=['name'])]
        verbose_name = "feature"
        verbose_name_plural = "features"

    def __str__(self):
        return f"{self.name}: {self.value}"


class Image(models.Model):
    """
    Stores product images and automatically converts them to WebP format.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='product')
    image_file = ResizedImageField(upload_to='products_images', quality=80, verbose_name='image')
    title = models.CharField(max_length=100, verbose_name='title')
    description = models.TextField(verbose_name='description')
    created = jmodels.jDateTimeField(auto_now_add=True, verbose_name='created at')

    class Meta:
        verbose_name = "image"
        verbose_name_plural = "images"
        ordering = ('created',)
        indexes = [models.Index(fields=['created'])]

    def __str__(self):
        return self.title or "Untitled"

    def save(self, *args, **kwargs):
        """
        Saves the image and converts it to optimized WebP format.
        """
        super().save(*args, **kwargs)  # First, save normally

        image_path = self.image_file.path

        # Open and convert to WebP
        img = PilImage.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")

        webp_path = os.path.splitext(image_path)[0] + ".webp"
        img.save(webp_path, "WEBP", quality=70, optimize=True, method=6)

        # Replace the original file with the WebP one
        os.remove(image_path)
        self.image_file.name = os.path.splitext(self.image_file.name)[0] + ".webp"

        # Update the image file path
        super().save(update_fields=["image_file"])

    def delete(self, *args, **kwargs):
        """
        Deletes the image file from storage when the model is deleted.
        """
        storage, path = self.image_file.storage, self.image_file.path
        storage.delete(path)
        super().delete(*args, **kwargs)


class Comment(models.Model):
    """
    Model for user comments on products.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments', verbose_name='product')
    user = models.ForeignKey(ShopUser, on_delete=models.CASCADE, related_name='comments', verbose_name='user')
    body = models.TextField(verbose_name="comment body")
    created = jmodels.jDateTimeField(auto_now_add=True, verbose_name='created at')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True, verbose_name='parent comment')

    class Meta:
        verbose_name = "comment"
        verbose_name_plural = "comments"
        ordering = ['-created']
        indexes = [models.Index(fields=['created'])]

    def __str__(self):
        return f"{self.user} — {self.product}"


class Rating(models.Model):
    """
    Rating model for storing user ratings on products.
    """
    product = models.ForeignKey(Product, related_name='ratings', on_delete=models.CASCADE, verbose_name='product')
    user = models.ForeignKey(ShopUser, related_name='ratings', on_delete=models.CASCADE, verbose_name='user')
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name='rating score')
    created = models.DateTimeField(auto_now_add=True, verbose_name='created at')
    updated = models.DateTimeField(auto_now=True, verbose_name='updated at')

    class Meta:
        verbose_name = "rating"
        verbose_name_plural = "ratings"
        unique_together = ('product', 'user')  # Each user can rate a product only once
        ordering = ['-updated']

    def __str__(self):
        return f'{self.product} — {self.user} — {self.score}'
