from django.contrib.postgres.search import TrigramSimilarity
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import TrigramSimilarity, SearchQuery
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
import json
from .models import *
from .forms import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.contrib import messages
from order.models import Order
# Create your views here.


def index(request):
    # return HttpResponse("Hello, world. You're at the polls index.")
    products_with_offer = Product.objects.filter(discount__gt=5)[:10]
    new_products = Product.objects.all().order_by('-created_at')[:10]
    favorite_products = Product.objects.all().order_by('-views')[:10]

    context = {
        "products_with_offer": products_with_offer,
        "new_products": new_products,
        "favorite_products": favorite_products,
    }
    return render(request, "shop/index.html", context)


def products_list(request):
    products = Product.objects.all()
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    try:
        products = paginator.get_page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = []
    context = {
        'products': products,
    }
    if request.headers.get('x-requested-With') == 'XMLHttpRequest':
        return  render(request, 'shop/products_list_ajax.html', context)

    return render(request, 'shop/products_list.html', context)

def product_detail(request, slug):
    product = Product.objects.get(slug=slug)
    related_product = Product.objects.filter(category=product.category).exclude(slug=product.slug)[:3]
    rating_percent = (float(product.average_rating) / 5.0) * 100 if product.rating_count else 0
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(product=product, user=request.user).score
        except Rating.DoesNotExist:
            user_rating = None

    form = CommentForm()

    product.views += 1
    product.save()
    context = {
        'product': product,
        'related_product': related_product,
        'form': form,
        'rating_percent': rating_percent,
        'user_rating': user_rating,
        'comments': Comment.objects.filter(product=product, parent__isnull=True)
    }
    return render(request, 'shop/product_detail.html', context)


def product_comments(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.product = product
        comment.user = request.user

        parent_id = request.POST.get('parent')
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id)
                comment.parent = parent_comment
            except Comment.DoesNotExist:
                return JsonResponse({'sent': False, 'error': 'Parent comment not found'}, status=404)

        comment.save()
        sent = True
        response_data = {
            'sent': True,
            'comment_id': comment.id,
            'parent': comment.parent.id if comment.parent else None,  # مهم
            'comment_user': comment.user.first_name,
            'comment_body': comment.body,
            'comment_create': comment.created.strftime('%Y-%m-%d %H:%M'),
        }
        return JsonResponse(response_data)

    else:
        return JsonResponse({
            'error':'problem' ,
            'sent' : False
        },
        status=400
        )


def products_list_discount(request):
    products = Product.objects.filter(discount__gt=0).order_by('-discount')
    paginator = Paginator(products, 20)
    page = request.GET.get('page')
    try:
        products = paginator.get_page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = []
    context = {
        'products': products,
    }
    if request.headers.get('x-requested-With') == 'XMLHttpRequest':
        return  render(request, 'shop/products_list_ajax.html', context)

    return render(request, 'shop/products_list.html', context)

def search(request):
    query = None
    result = []
    if "query" in request.GET:
        form = SearchForm(data=request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            search_query = SearchQuery(query)
            # using TrigramSimilarity
            result_1 = Product.objects.annotate(similarity=TrigramSimilarity("name", query)).\
            filter(similarity__gt=0.2).order_by("-similarity")
            result_2 = Product.objects.annotate(similarity=TrigramSimilarity("description", query)).\
            filter(similarity__gt=0.2).order_by("-similarity")

            result = result_1 | result_2

    context = {
        "query": query,
        "result": result
    }
    return render(request, "shop/search.html", context)


@require_POST
def rate_product(request, pk):
    """
    درخواست POST برای ثبت یا بروزرسانی امتیاز کاربر برای محصول pk.
    انتظار دارد JSON یا فرم-انکد شده ارسال شود: { "score": 4, "comment": "..." }
    """
    product = get_object_or_404(Product, pk=pk)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required', 'login_url': settings.LOGIN_URL}, status=401)

    # پذیرش JSON یا form-data
    if request.content_type and 'application/json' in request.content_type:
        try:
            data = json.loads(request.body.decode())
        except Exception:
            return JsonResponse({'error': 'invalid_json'}, status=400)
    else:
        data = request.POST

    score = data.get('score')
    comment = data.get('comment', '')

    try:
        score = int(score)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'invalid_score'}, status=400)

    if score < 1 or score > 5:
        return JsonResponse({'error': 'invalid_score_range'}, status=400)

    with transaction.atomic():
        rating, created = Rating.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'score': score}
        )
        # آپدیت میانگین و تعداد در محصول (درصورتی که از denormalized استفاده کنی)
        product.update_rating()

    return JsonResponse({
        'success': True,
        'average': float(product.average_rating),
        'count': product.rating_count,
        'user_score': rating.score
    })

