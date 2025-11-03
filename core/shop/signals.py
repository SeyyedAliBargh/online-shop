from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Product

@receiver(pre_save, sender=Product)
def calculate_new_price(sender, instance, **kwargs):
    if instance.discount is not None:
        try:
            instance.discount_price = int(instance.original_price * (100 - instance.discount) / 100)
        except (TypeError, ValueError):
            instance.discount_price = instance.original_price
    else:
        instance.discount_price = instance.original_price