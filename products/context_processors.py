# products/context_processors.py

from .models import Category

def all_categories(request):
    categories = Category.objects.all()
    return {'categories': categories}
