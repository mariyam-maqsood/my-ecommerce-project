from django.urls import path

from . import views

urlpatterns = [
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/increase/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('cart/decrease/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('product/<int:id>/buy_now/', views.buy_now, name='buy_now'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('stripe-checkout/', views.create_checkout_session, name='stripe_checkout'),
    path('success-stripe/', views.stripe_success, name='stripe_success'),
    # path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('history/', views.order_history, name='order_history'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),




]
