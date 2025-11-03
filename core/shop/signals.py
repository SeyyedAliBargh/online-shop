from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Product


@receiver(pre_save, sender=Product)
def calculate_new_price(sender, instance, **kwargs):
    """
    🔔 Signal: pre_save for Product model

    This function runs automatically **before** a Product instance is saved.

    Purpose:
        - Automatically calculate the `discount_price` field
          based on `original_price` and `discount` percentage.

    Behavior:
        - If a discount exists, it calculates the discounted price.
        - If the discount is missing, the discounted price equals the original price.
        - If invalid or non-numeric data is provided, it safely falls back to the original price.
    """

    # Check if the product has a discount value
    if instance.discount is not None:
        try:
            # Calculate discounted price:
            # Formula → discounted_price = original_price × (100 - discount) ÷ 100
            instance.discount_price = int(
                instance.original_price * (100 - instance.discount) / 100
            )
        except (TypeError, ValueError):
            # In case of invalid input (non-numeric values), fall back to original price
            instance.discount_price = instance.original_price
    else:
        # No discount → keep discounted price equal to original price
        instance.discount_price = instance.original_price
