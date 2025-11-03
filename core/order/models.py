from django.db import models
from django.db import models
from account.models import ShopUser
from shop.models import Product
# from coupon.models import Coupon

# Create your models here.

# Create your models here.

class Order(models.Model):
    buyer = models.ForeignKey(ShopUser, on_delete=models.SET_NULL, related_name="orders", null=True)
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    phone = models.CharField(max_length=11)
    address = models.CharField(max_length=250)
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=50)
    province = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    paid = models.BooleanField(default=False)
    ref_id = models.CharField(max_length=100, default="")
    # coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, blank=True, null=True)
    discount = models.IntegerField(default=0)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"


        ordering = ['-created']
        indexes = [
            models.Index(
                fields=['-created'],
            )
        ]
    def __str__(self):
        return f"order {self.id}"


    def get_total_cost(self):
        total = sum(item.get_cost() for item in self.items.all())
        return total - (total * (self.discount / 100))

    def get_post_cost(self):
        # درمورد قیمت هزینه پستی در کشور تحقیق کن
        weight = sum(item.get_weight() for item in self.items.all())
        if weight < 1000:
            return 20000
        elif 1000 <= weight < 2000:
            return 30000
        else:
            return 50000

    def get_final_cost(self):
        return self.get_total_cost() + self.get_post_cost()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='order_items')
    price = models.PositiveIntegerField(default=0)
    quantity = models.PositiveIntegerField(default=1)
    weight = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ایتم سفارش"
        verbose_name_plural = "ایتم های سفارشات"

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        return self.price * self.quantity

    def get_weight(self):
        return self.weight * self.quantity
