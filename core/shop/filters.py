import django_filters
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    # قیمت
    min_price = django_filters.NumberFilter(field_name='original_price', lookup_expr='gte', label='قیمت حداقل')
    max_price = django_filters.NumberFilter(field_name='original_price', lookup_expr='lte', label='قیمت حداکثر')

    # برند به صورت انتخابی
    BRAND_CHOICES = Product.objects.values_list('brand', 'brand').distinct()
    brand = django_filters.ChoiceFilter(choices=[], label='برند')

    # دسته بندی به صورت انتخابی
    # category = django_filters.ModelChoiceFilter(
    #     queryset=Category.objects.all(),
    #     label='دسته بندی'
    # )

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'brand', 'category']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تنظیم choices دینامیک
        brands = Product.objects.values_list('brand', 'brand').distinct()
        self.filters['brand'].extra['choices'] = [(b[0], b[0]) for b in brands if b[0]]

        # categories = Category.objects.values_list('name', 'name').distinct()
        # self.filters['category'].extra['choices'] = [(c[0], c[0]) for c in categories if c[0]]