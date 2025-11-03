from django.db import models
import os
from PIL import Image as PilImage
from django.urls import reverse
from account.models import ShopUser
from django.db import models
from django.utils.text import slugify
from django_resized import ResizedImageField
from django_jalali.db import models as jmodels
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg, Count
from mptt.models import MPTTModel, TreeForeignKey
from django.utils import timezone
from account.models import ShopUser




# Create your models here.
class Category(MPTTModel):
    name = models.CharField(max_length=100, verbose_name='دسته بندی')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='اسلاگ')
    parent = TreeForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='children',
        null=True,
        blank=True,
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        while k is not None:
            full_path.append(k.name)
            k = k.parent
        return ' → '.join(full_path[::-1])


class Product(models.Model):
    """
    This model manages 'products' and creates a new `Product` instance.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    inventory = models.PositiveIntegerField(default=0, verbose_name='موجودی')

    name = models.CharField(max_length=100, verbose_name='نام محصول')
    description = models.TextField(verbose_name='توضیحات')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='اسلاگ')

    weight = models.PositiveIntegerField(default=0)
    brand = models.CharField(max_length=250, blank=True, null=True)
    original_price = models.PositiveIntegerField(default=0, verbose_name='قیمت')
    discount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="درصد تخفیف بین ۰ تا ۱۰۰",
        null=True,
        blank=True
    )
    discount_price = models.PositiveIntegerField(default=0, verbose_name='قیمت بعد از تخقیف', null=True, blank=True)
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')
    updated_at = jmodels.jDateTimeField(auto_now=True, verbose_name='زمان اپدیت')
    views = models.PositiveIntegerField(default=0, verbose_name='تعداد بازدید')
    sold_count = models.PositiveIntegerField(default=0)

    # product rating
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('name',)
        indexes = [models.Index(fields=['name'])]

        verbose_name = 'محصول'
        verbose_name_plural = 'محصولات'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """
         Returns the absolute URL for the product detail page.

         This method uses Django's `reverse` function to generate the URL
         based on the product's slug and the named URL pattern 'shop:product_detail'.

        Returns:
        str: The absolute URL of the product detail page.
        """
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """
        This function creates slugs based on product name.
        """
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Deletes the product instance and removes all associated image files from storage.

        This method overrides the default delete behavior to ensure that all image files
        linked to the product are explicitly deleted from the file system before the
        database record is removed.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """

        for img in self.images.all():
            storage, path = img.image_file.storage, img.image_file.path
            storage.delete(path)
        super().delete(*args, **kwargs)

    def update_rating(self):
        """
        Updates the average rating and rating count for the object.

        This method calculates the average score and total number of ratings
        from the related `ratings` queryset using Django's aggregation functions.
        It then updates the `average_rating` and `rating_count` fields and saves
        the changes to the database.

        Returns:
            None
        """

        agg = self.ratings.aggregate(avg=Avg('score'), count=Count('id'))
        self.average_rating = agg['avg'] or 0
        self.rating_count = agg['count'] or 0
        self.save(update_fields=['average_rating', 'rating_count'])





class ProductFeature(models.Model):
    """
    This model manages product features and creates a new `ProductFeature` instance.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    name = models.CharField(max_length=100, verbose_name='ویژگی')
    value = models.CharField(max_length=250, verbose_name='مقدار')

    class Meta:
        verbose_name = "ویژگی"
        verbose_name_plural = "ویژگی ها"


        ordering = ('name',)
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name





class Image(models.Model):
    """
    This model creates product-related images.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image_file = ResizedImageField(upload_to='products_images', quality=80, verbose_name='عکس')
    title = models.CharField(max_length=100, verbose_name='عنوان')
    description = models.TextField(verbose_name='توضیحات')
    created = jmodels.jDateTimeField(auto_now_add=True, verbose_name='زمان ایجاد')

    class Meta:
        verbose_name = "تصویر"
        verbose_name_plural = "تصاویر"
        ordering = ('created',)
        indexes = [models.Index(fields=['created'])]

    def __str__(self):
        return self.title if self.title else "None"

    def save(self, *args, **kwargs):
        """
        This function changes the image to webp
        """
        super().save(*args, **kwargs)  # اول ذخیره‌ی عادی

        # مسیر فایل اصلی
        image_path = self.image_file.path

        # باز کردن و تبدیل به WebP
        img = PilImage.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")

        webp_path = os.path.splitext(image_path)[0] + ".webp"
        img.save(webp_path, "WEBP", quality=70, optimize=True, method=6)

        # جایگزین کردن فایل اصلی با webp
        os.remove(image_path)
        self.image_file.name = os.path.splitext(self.image_file.name)[0] + ".webp"

        super().save(update_fields=["image_file"])  # ذخیره دوباره برای آپدیت مسیر

    def delete(self, *args, **kwargs):
        storage, path = self.image_file.storage, self.image_file.path
        storage.delete(path)
        super().delete(*args, **kwargs)





class Comment(models.Model):
    """
    This model creates product-related comments and their replies.
    """
    product = models.ForeignKey(Product , on_delete=models.CASCADE , related_name='comments')
    user = models.ForeignKey(ShopUser, on_delete=models.CASCADE, related_name='comments')
    body = models.TextField(verbose_name="دیدگاه")
    created = jmodels.jDateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name='replies', null=True, blank=True)
    # active = models.BooleanField(default=True)


    class Meta:

        verbose_name = "نظر"
        verbose_name_plural = "نظرات"
        ordering = ['-created']
        indexes = [
            models.Index(fields=['created']),
        ]

    def __str__(self):
        return f"{self.user} : {self.product}"


class Rating(models.Model):
    """
    This model gives a score to the user for buying a product.
    """
    product = models.ForeignKey(Product, related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(ShopUser, related_name='ratings', on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:

        verbose_name = "امتیاز"
        verbose_name_plural = "امتیازات"
        unique_together = ('product', 'user')  # هر کاربر یک امتیاز به ازای هر محصول
        ordering = ['-updated']

    def __str__(self):
        return f'{self.product} — {self.user} — {self.score}'