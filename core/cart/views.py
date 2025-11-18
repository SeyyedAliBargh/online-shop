import traceback

from django.contrib.messages.api import success
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
from django.shortcuts import redirect
from order.models import Order


# Create your views here.
def detail_cart(request):
    cart = Cart(request)
    similar_products = []
    for item in cart:
        product = item['product']
        # پیدا کردن محصولات مشابه بر اساس دسته‌بندی
        similars = Product.objects.filter(
            category=product.category
        ).exclude(id=product.id)[:4]
        similar_products.extend(similars)
    similar_products = list(set(similar_products))
    print(similar_products)
    context = {
        'cart': cart,
        'similar_products': similar_products,
    }
    return render(request, 'cart/detail_cart.html', context)

@require_POST
def add(request, product_id):
    try:
        product = Product.objects.get(id = product_id)
        cart = Cart(request)
        cart.add(product)
        context = {
            'item_count': len(cart),
            'get_total_price': cart.get_total_price()
        }
        return JsonResponse(context)

    except Exception as e:

        print("خطا در افزودن به سبد خرید:", e)

        traceback.print_exc()

        return JsonResponse({'error': 'مشکلی پیش آمد'}, status=500)


@require_POST
def update_quantity(request):
    product_id = request.POST['product_id']
    action = request.POST['action']
    try:
        product = Product.objects.get(id=product_id)
        cart = Cart(request)
        if action == 'add':
            cart.add(product)
        elif action == 'decrease':
            cart.decrease(product)

        product_cost = cart.cart[product_id]['quantity'] * cart.cart[product_id]['price']
        context = {
            'success': True,
            'product_cost': product_cost,
            'item_count': len(cart),
            'get_total_price': cart.get_total_price(),
            'get_post_price': cart.get_post_price(),
            'quantity': cart.cart[product_id]['quantity'],
            'get_final_price': cart.get_final_price(),
        }

        return JsonResponse(context)

    except:
        return JsonResponse({'error': 'Something went wrong'})


def delete_product(request):
    try:
        product_id = request.POST['product_id']
        product = Product.objects.get(id=product_id)
        cart = Cart(request)
        cart.delete(product)
        context = {
            'success': True,
            'item_count': len(cart),
            'get_final_price': cart.get_final_price(),
            'get_post_price': cart.get_post_price(),
            'get_total_price': cart.get_total_price(),
        }
        return JsonResponse(context)
    except:
        return JsonResponse({'error': 'Something went wrong'})

