from django.views import View
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category


def is_admin(user):
    """Check if the user has staff privileges."""
    return user.is_staff


class ProductListView(View):
    """View to list all available products on the home page."""

    def get(self, request):
        products = Product.objects.all()
        return render(request, 'products/home.html',
                {'products': products})


def product_detail(request, id):
    """Display details for a single product and check stock availability."""
    product = get_object_or_404(Product, id=id)

    if product.stock <= 0:
        messages.error(request, "Out of stock!")

    return render(
        request, 'products/product_detail.html',
        {'product': product}
    )


def all_categories(request):
    """Context processor to provide all categories to templates."""
    categories = Category.objects.all()
    return {'categories': categories}


def category_products(request, id):
    """Filter and display products belonging to a specific category."""
    category = get_object_or_404(Category, id=id)
    products = Product.objects.filter(category=category)
    return render(
        request,
        'products/home.html',
        {'products': products, 'selected_category': category}
    )