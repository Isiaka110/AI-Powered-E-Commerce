import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .forms import SignUpForm
from .models import Product, Order, OrderItem, Cart, CartItem # Added Cart models
from decimal import Decimal

# --- CLIENT VIEWS ---

def landing_page(request):
    return render(request, 'store/landing.html')

def personalized_signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'store/signup.html', {'form': form})

@login_required
def dashboard(request):
    user_size = request.user.preferred_size
    recommendations = Product.objects.filter(size=user_size, is_available=True).order_by('-created_at')
    if not recommendations.exists():
        recommendations = Product.objects.filter(is_available=True).order_by('-created_at')
    
    return render(request, 'store/dashboard.html', {
        'products': recommendations,
        'user_size': user_size
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(
        category=product.category, 
        is_available=True
    ).exclude(id=product.id)[:4]
    
    return render(request, 'store/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

# --- WISHLIST ---

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.favorites.filter(id=request.user.id).exists():
        product.favorites.remove(request.user)
    else:
        product.favorites.add(request.user)
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

@login_required
def wishlist_view(request):
    products = request.user.favorites.all()
    return render(request, 'store/wishlist.html', {'products': products})

# --- NEW DATABASE-BACKED CART VIEWS ---

@login_required
def add_to_cart(request, product_id):
    """Adds item to database Cart instead of session."""
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()
        
    return redirect('cart')

@login_required
def cart_view(request):
    """Fetches CartItems from DB. item.id now exists for the template buttons."""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    
    total = sum(item.get_total for item in cart_items)
    
    discount = 0
    coupon_error = None
    if request.method == 'POST':
        code = request.POST.get('coupon_code')
        if code == 'THRIFT20':
            discount = total * Decimal('0.20')
        else:
            coupon_error = "Invalid Coupon Code"

    context = {
        'cart_items': cart_items,
        'total': total,
        'discount': discount,
        'grand_total': total - discount,
        'coupon_error': coupon_error
    }
    return render(request, 'store/cart.html', context)

@login_required
def update_cart_quantity(request, item_id, action):
    # Try to get the item, but don't crash if it's already gone
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return redirect('cart')
    
    # Check if we should delete it immediately (from the "Remove Item" link)
    if request.GET.get('remove') == 'true':
        cart_item.delete()
        return redirect('cart')

    if action == 'increment':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrement':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
            
    return redirect('cart')

@login_required
def complete_purchase(request):
    """Converts DB cart into permanent Order."""
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()
    
    if not cart_items.exists():
        return redirect('dashboard')

    order = Order.objects.create(
        user=request.user,
        order_id=str(uuid.uuid4())[:12].upper(),
        total_paid=0,
        is_completed=True
    )

    grand_total = 0
    for item in cart_items:
        OrderItem.objects.create(
            order=order, 
            product=item.product, 
            price=item.product.current_price, 
            quantity=item.quantity
        )
        grand_total += item.get_total
        
    order.total_paid = grand_total
    order.save()

    # Clear DB cart after purchase
    cart_items.delete()
    
    return render(request, 'store/success.html', {'order': order})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/order_history.html', {'orders': orders})

import requests # You'll need this: pip install requests

@login_required
def complete_purchase(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()
    
    if not cart_items.exists():
        return redirect('dashboard')

    total_amount = sum(item.get_total for item in cart_items)
    
    # This is where you would normally call the Paystack API
    # For now, we simulate the order creation
    order = Order.objects.create(
        user=request.user,
        order_id=str(uuid.uuid4())[:12].upper(),
        total_paid=total_amount,
        is_completed=True
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order, 
            product=item.product, 
            price=item.product.current_price, 
            quantity=item.quantity
        )
    
    # Clear cart
    cart_items.delete()
    
    return render(request, 'store/success.html', {'order': order})

# --- OWNER / ADMIN VIEWS ---

@staff_member_required
def owner_dashboard(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'store/owner_dashboard.html', {'products': products})

@staff_member_required
def delete_product(request, product_id):
    get_object_or_404(Product, id=product_id).delete()
    return redirect('owner_dashboard')

@staff_member_required
def toggle_availability(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_available = not product.is_available
    product.save()
    return redirect('owner_dashboard')