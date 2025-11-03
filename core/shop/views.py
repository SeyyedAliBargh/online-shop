import json
from django.conf import settings
from django.contrib.postgres.search import SearchQuery, TrigramSimilarity
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from shop.forms import SearchForm, CommentForm
from shop.models import Product, Rating, Comment, Category


# -----------------------------
# Basic index view (for testing)
# -----------------------------
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


# ---------------------------------
# Display list of all products (paginated)
# ---------------------------------
def products_list(request):
    products = Product.objects.all()
    paginator = Paginator(products, 20)  # Show 20 products per page
    page = request.GET.get('page')
    categories = Category.objects.all()

    try:
        products = paginator.get_page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = []

    context = {'products': products}

    # Handle AJAX request (for infinite scroll or dynamic load)
    if request.headers.get('x-requested-With') == 'XMLHttpRequest':
        return render(request, 'shop/products_list_ajax.html', context)

    return render(request, 'shop/product_list.html', context)


# -------------------------------------------------
# Product detail page + related items + comments + rating
# -------------------------------------------------
def product_detail(request, slug):
    # Get product by slug
    product = Product.objects.get(slug=slug)

    # Get up to 3 related products from the same category
    related_product = Product.objects.filter(category=product.category).exclude(slug=product.slug)[:3]

    # Calculate rating percent (for display in stars or progress bar)
    rating_percent = (float(product.average_rating) / 5.0) * 100 if product.rating_count else 0

    # Get the user's own rating if authenticated
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(product=product, user=request.user).score
        except Rating.DoesNotExist:
            user_rating = None

    # Initialize empty comment form
    form = CommentForm()

    # Count views
    product.views += 1
    product.save()

    context = {
        'product': product,
        'related_product': related_product,
        'form': form,
        'rating_percent': rating_percent,
        'user_rating': user_rating,
        'comments': Comment.objects.filter(product=product, parent__isnull=True),
    }

    return render(request, 'shop/product_detail.html', context)


# -------------------------------------------------
# Add new comment (and handle replies via parent ID)
# -------------------------------------------------
def product_comments(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = CommentForm(request.POST)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.product = product
        comment.user = request.user

        # Handle nested (reply) comments
        parent_id = request.POST.get('parent')
        if parent_id:
            try:
                parent_comment = Comment.objects.get(id=parent_id)
                comment.parent = parent_comment
            except Comment.DoesNotExist:
                return JsonResponse({'sent': False, 'error': 'Parent comment not found'}, status=404)

        comment.save()

        # Prepare JSON response for AJAX
        response_data = {
            'sent': True,
            'comment_id': comment.id,
            'parent': comment.parent.id if comment.parent else None,  # Important for replies
            'comment_user': comment.user.first_name,
            'comment_body': comment.body,
            'comment_create': comment.created.strftime('%Y-%m-%d %H:%M'),
        }
        return JsonResponse(response_data)

    else:
        # If form validation fails
        return JsonResponse({'error': 'problem', 'sent': False}, status=400)


# -------------------------------------------------
# List products that have discounts (ordered by discount)
# -------------------------------------------------
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

    context = {'products': products}

    # AJAX support for asynchronous loading
    if request.headers.get('x-requested-With') == 'XMLHttpRequest':
        return render(request, 'shop/products_list_ajax.html', context)

    return render(request, 'shop/products_list.html', context)


# -------------------------------------------------
# Full-text search with PostgreSQL TrigramSimilarity
# -------------------------------------------------
def search(request):
    query = None
    result = []

    if "query" in request.GET:
        form = SearchForm(data=request.GET)
        if form.is_valid():
            query = form.cleaned_data["query"]
            search_query = SearchQuery(query)

            # Search similar names
            result_1 = Product.objects.annotate(
                similarity=TrigramSimilarity("name", query)
            ).filter(similarity__gt=0.2).order_by("-similarity")

            # Search similar descriptions
            result_2 = Product.objects.annotate(
                similarity=TrigramSimilarity("description", query)
            ).filter(similarity__gt=0.2).order_by("-similarity")

            # Merge both result sets
            result = result_1 | result_2

    context = {
        "query": query,
        "result": result
    }

    return render(request, "shop/search.html", context)


# -------------------------------------------------
# Handle user rating for a product via AJAX (POST)
# -------------------------------------------------
@require_POST
def rate_product(request, pk):
    """
    Handle POST request to create or update a user's rating for a given product.
    Expected data (JSON or form-encoded):
        {"score": 4, "comment": "optional comment"}
    """

    product = get_object_or_404(Product, pk=pk)

    # User must be logged in
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'login_required', 'login_url': settings.LOGIN_URL}, status=401)

    # Accept both JSON and form-data requests
    if request.content_type and 'application/json' in request.content_type:
        try:
            data = json.loads(request.body.decode())
        except Exception:
            return JsonResponse({'error': 'invalid_json'}, status=400)
    else:
        data = request.POST

    # Extract and validate score
    score = data.get('score')
    comment = data.get('comment', '')

    try:
        score = int(score)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'invalid_score'}, status=400)

    if score < 1 or score > 5:
        return JsonResponse({'error': 'invalid_score_range'}, status=400)

    # Save or update rating atomically
    with transaction.atomic():
        rating, created = Rating.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'score': score}
        )

        # Update product's average rating and rating count
        product.update_rating()

    # Return updated rating info to frontend
    return JsonResponse({
        'success': True,
        'average': float(product.average_rating),
        'count': product.rating_count,
        'user_score': rating.score
    })
