import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from products.models import Product
from .forms import CheckoutForm
from .models import Cart, CartItem, Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def calculate_cart_total(cart_items):
    """Calculate the total price of all items in the cart."""
    return sum(item.product.price * item.quantity for item in cart_items)


@login_required
def add_to_cart(request, product_id):
    """Add a specific product to the user's cart."""
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product
    )

    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(
                request, f"Added another {product.name} to your cart."
            )
        else:
            messages.error(request, "Stock limit reached!")
    else:
        messages.success(request,
                f"{product.name} added to your cart.")

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('product_detail', id=product.id)


@login_required
def view_cart(request):
    """Display the items in the current user's cart."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'orders/cart.html',
                {'cart': cart})


@login_required
def increase_quantity(request, item_id):
    """Increment the quantity of an item in the cart."""
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if item.quantity < item.product.stock:
        item.quantity += 1
        item.save()
    else:
        messages.error(request, "No more stock available!")
    return redirect('view_cart')


@login_required
def decrease_quantity(request, item_id):
    """Decrement the quantity or remove an item if quantity is 1."""
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if item.quantity > 1:
        item.quantity -= 1
        item.save()
    else:
        item.delete()
    return redirect('view_cart')


@login_required
def buy_now(request, id):
    """Force cart quantity to 1 for a product and redirect to checkout."""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=id)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, product=product
        )
        if not created:
            cart_item.quantity = 1
            cart_item.save()

        return redirect('checkout')

    return redirect('product_detail', id=id)


@login_required
def checkout(request):
    """Handle the checkout process for both CARD and COD payments."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()

    if not cart_items:
        return redirect('home')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        payment_method = request.POST.get('payment_method')

        if form.is_valid():
            total_amount = calculate_cart_total(cart_items)

            if payment_method == 'CARD':
                request.session['checkout_form'] = form.cleaned_data
                return redirect('stripe_checkout')

            order = form.save(commit=False)
            order.user = request.user
            order.total = total_amount
            order.payment_method = 'COD'
            order.save()

            for item in cart_items:
                if item.product.stock < item.quantity:
                    messages.error(
                        request,
                        f"Not enough stock for {item.product.name}"
                    )
                    return redirect('view_cart')

                item.product.stock -= item.quantity
                item.product.save()

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    subtotal=item.product.price * item.quantity
                )

            cart.items.all().delete()
            send_order_email(order)
            return redirect('order_success', order_id=order.id)
    else:
        form = CheckoutForm(initial={
            'name': request.user.get_full_name(),
            'email': request.user.email
        })

    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart_items': cart_items
    })


@login_required
def place_order(request):
    """Clear session-based cart and display success message."""
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('home')

    request.session['cart'] = {}
    return render(request, 'orders/order_success.html')


@login_required
def order_success(request, order_id):
    """Display confirmation page for a specific order."""
    order = Order.objects.get(id=order_id)
    return render(request, 'orders/order_success.html',
            {'order': order})


@login_required
def create_checkout_session(request):
    """Initiate a Stripe Checkout Session."""
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('product').all()
    line_items = []

    for item in cart_items:
        line_items.append({
            'price_data': {
                'currency': 'pkr',
                'product_data': {'name': item.product.name},
                'unit_amount': int(item.product.price * 100),
            },
            'quantity': item.quantity,
        })

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url='http://127.0.0.1:8000/orders/success-stripe/',
        cancel_url='http://127.0.0.1:8000/cart/',
        metadata={'user_id': request.user.id}
    )

    return redirect(session.url, code=303)


# @login_required
# def stripe_success(request):
#     """Handle successful Stripe redirection and create Order record."""
#     cart, _ = Cart.objects.get_or_create(user=request.user)
#     cart_items = cart.items.select_related('product').all()
#     form_data = request.session.get('checkout_form')
#
#     if not form_data or not cart_items.exists():
#         return redirect('checkout')
#
#     total_amount = calculate_cart_total(cart_items)
#     order = Order.objects.create(
#         user=request.user,
#         total=total_amount,
#         payment_method='CARD',
#         **form_data
#     )
#
#     for item in cart_items:
#         OrderItem.objects.create(
#             order=order,
#             product=item.product,
#             quantity=item.quantity,
#             subtotal=item.product.price * item.quantity
#         )
#         item.product.stock -= item.quantity
#         item.product.save()
#
#     cart.items.all().delete()
#     send_order_email(order)
#     del request.session['checkout_form']
#
#     return redirect('order_success', order_id=order.id)
#
# @csrf_exempt
# def stripe_webhook(request):
#     """Handle Stripe webhook events for asynchronous payment verification."""
#     payload = request.body
#     sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
#     endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
#
#     try:
#         event = stripe.Webhook.construct_event(
#             payload, sig_header, endpoint_secret
#         )
#     except (ValueError, stripe.error.SignatureVerificationError):
#         return HttpResponse(status=400)
#
#     print('PRINTING EVENTSSSS!!!')
#     print('Event:', event)
#
#     if event['type'] == 'checkout.session.completed':
#         # print('PRINTING EVENTSSSS!!!')
#         # print('Event:',event)
#
#         session = event['data']['object']
#         user_id = session['metadata']['user_id']
#
#         user_id = session.get('metadata', {}).get('user_id')
#         if not user_id:
#             return HttpResponse(status=400)
#         session_id = session['id']
#
#         User = get_user_model()
#         user = User.objects.get(id=user_id)
#
#         cart, _ = Cart.objects.get_or_create(user=user)
#         cart_items = cart.items.select_related('product').all()
#
#         if not cart_items.exists():
#             return HttpResponse(status=200)
#
#         order = Order.objects.create(
#             user=user,
#             total=calculate_cart_total(cart_items),
#             payment_method='CARD',
#             name=session['customer_details']['name'],
#             email=session['customer_details']['email'],
#         )
#
#         for item in cart_items:
#             OrderItem.objects.create(
#                 order=order,
#                 product=item.product,
#                 quantity=item.quantity,
#                 subtotal=item.product.price * item.quantity
#             )
#             item.product.stock -= item.quantity
#             item.product.save()
#
#         cart.items.all().delete()
#         send_order_email(order)
#
#     return HttpResponse(status=200)

@login_required
def stripe_success(request):
    """Redirect user to their most recent order after successful Stripe payment."""
    # Wait briefly for webhook to fire and create the order
    import time
    time.sleep(2)

    order = Order.objects.filter(user=request.user).order_by(
        '-created_at').first()
    if not order:
        return redirect('checkout')

    return redirect('order_success', order_id=order.id)


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhook events - single source of truth for order creation."""
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header,
                                               endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        session_id = session['id']

        # Idempotency: skip if this session was already processed
        if Order.objects.filter(stripe_session_id=session_id).exists():
            return HttpResponse(status=200)

        user_id = session.get('metadata', {}).get('user_id')
        if not user_id:
            return HttpResponse(status=400)

        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return HttpResponse(status=400)

        cart, _ = Cart.objects.get_or_create(user=user)
        cart_items = cart.items.select_related('product').all()

        if not cart_items.exists():
            return HttpResponse(status=200)

        order = Order.objects.create(
            user=user,
            stripe_session_id=session_id,
            total=calculate_cart_total(cart_items),
            payment_method='CARD',
            name=session['customer_details']['name'],
            email=session['customer_details']['email'],
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                subtotal=item.product.price * item.quantity
            )
            item.product.stock -= item.quantity
            item.product.save()

        cart.items.all().delete()

        try:
            send_order_email(order)
        except Exception as e:
            print(f"Order email failed: {e}")

    return HttpResponse(status=200)


def send_order_email(order):
    """Send HTML order confirmation email to the user."""
    subject = f"Order Confirmation #{order.id}"
    message = render_to_string("orders/order_email.html",
                {"order": order})
    email = EmailMessage(subject, message, None, [order.email])
    email.content_subtype = "html"
    email.send(fail_silently=False)


@login_required
def order_history(request):
    """Display list of past orders for the authenticated user."""
    orders = Order.objects.filter(user=request.user).order_by('-id')
    return render(request, 'orders/order_history.html',
                  {'orders': orders})


@login_required
def cancel_order(request, order_id):
    """Cancel a pending order and restore product stock."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == "POST":
        if str(order.status).strip().capitalize() == 'Pending':
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()

            order.status = 'Cancelled'
            order.save()
            send_cancel_email(order)
            messages.success(request, "Order cancelled successfully.")
        else:
            messages.error(
                request,
                f"Cannot cancel order with status: {order.status}"
            )

    return redirect('order_history')


def send_cancel_email(order):
    """Send HTML cancellation email to the user."""
    subject = f"Order Cancelled #{order.id}"
    message = render_to_string("orders/cancel_email.html",
                {"order": order})
    email = EmailMessage(subject, message, None, [order.email])
    email.content_subtype = "html"
    email.send(fail_silently=False)