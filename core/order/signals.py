from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, OrderItem
from shop.models import Product
from django.db.models.signals import post_save

@receiver(post_save, sender=Order)
def update_product_sold_count(sender, instance, created, **kwargs):
    if created:
        for item in instance.items.all():  # items همان related_name
            product = item.product
            product.sold_count += item.quantity
            product.save()
