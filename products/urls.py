from django.urls import path
from . import views
from .views import ProductListView


urlpatterns = [
    path(
        '',
        ProductListView.as_view(),
        name='home'
    ),
    path(
        'product/<int:id>/',
        views.product_detail,
        name='product_detail'
    ),
    path(
        'category/<int:id>/',
        views.category_products,
        name='category_products'
    ),
]