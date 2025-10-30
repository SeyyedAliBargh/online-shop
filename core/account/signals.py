from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, ShopUser


@receiver(post_save, sender=ShopUser)
def create_profile(sender, instance, created, **kwargs):
    """
    create a Profile instance for each user
    :param sender:
    :param instance:
    :param created:
    :param kwargs:
    :return:
    """
    if created:
        Profile.objects.create(user=instance)