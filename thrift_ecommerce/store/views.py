import uuid
from decimal import Decimal
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import SignUpForm, ProductForm, StoreSettingsForm, VendorOnboardingStepOneForm
from .models import Product, Order, OrderItem, Cart, CartItem, StoreSettings, PromoCode, VendorProfile
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tokens import account_activation_token

# --- HELPER: CHECK IF OWNER ---
def is_owner(user):
    return user.is_superuser or user.is_staff

# --- CLIENT VIEWS ---

def landing_page(request):
    # Fetch recent products for the "Fresh Drops" section on landing
    recent_products = Product.objects.filter(is_available=True).order_by('-created_at')[:4]
    return render(request, 'store/landing.html', {'recent_products': recent_products})

def personalized_signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('vendor_onboarding')
    else:
        form = SignUpForm()
    return render(request, 'store/signup.html', {'form': form})

@login_required
def dashboard(request):
    user_size = request.user.preferred_size
    # AI Logic: Prioritize user's size, but show everything available
    all_available = Product.objects.filter(is_available=True).order_by('-created_at')
    
    # Filter for exact matches to highlight them in the UI if needed
    recommended = all_available.filter(size=user_size)
    
    return render(request, 'store/dashboard.html', {
        'products': all_available, # Show all, but you can highlight recommended in template
        'recommended': recommended,
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



def terms_and_conditions(request):
    return render(request, 'store/terms.html')


def vendor_onboarding(request):
    if not request.user.is_authenticated:
        return redirect('login')

    profile = VendorProfile.objects.filter(user=request.user).first()
    step = request.GET.get('step', '1')

    if request.method == 'POST' and step == '1':
        form = VendorOnboardingStepOneForm(request.POST, instance=profile)
        if form.is_valid():
            vendor_profile = form.save(commit=False)
            vendor_profile.user = request.user
            vendor_profile.save()
            messages.success(request, 'Step 1 complete. Your storefront is now provisioned.')
            return redirect(f"{request.path}?step=2")
    else:
        form = VendorOnboardingStepOneForm(instance=profile)

    if step == '2' and not profile:
        messages.warning(request, 'Complete step 1 to generate your storefront slug.')
        return redirect(f"{request.path}?step=1")

    return render(request, 'store/vendor_onboarding.html', {
        'step': step,
        'form': form,
        'profile': profile,
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
def wishlist(request):
    products = request.user.favorites.all()
    return render(request, 'store/wishlist.html', {'products': products})

# --- DATABASE-BACKED CART ---

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not product.is_available or product.quantity == 0:
        messages.warning(request, f"{product.name} is currently out of stock.")
        return redirect('dashboard')

    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)

    if item_created:
        messages.success(request, f"Added {product.name} to your bag.")
    elif cart_item.quantity < product.quantity:
        cart_item.quantity += 1
        cart_item.save()
    else:
        messages.warning(request, f"Only {product.quantity} units available for {product.name}.")

    return redirect('cart')

# store/views.py

def shop_view(request):
    # This ensures "Sold Out" or hidden products don't appear in the grid
    products = Product.objects.filter(is_available=True)
    return render(request, 'store/dashboard.html', {'products': products})

@login_required
def cart_view(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total = cart.total_price
    
    discount = Decimal('0.00')
    coupon_error = None
    if request.method == 'POST':
        code = (request.POST.get('coupon_code') or '').strip()
        promo = PromoCode.objects.filter(code__iexact=code, is_active=True).first()
        if promo:
            discount_rate = Decimal(promo.discount_percentage) / Decimal('100')
            discount = (total * discount_rate).quantize(Decimal('0.01'))
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
    # Try to get the item, but don't crash if it's not found
    cart_item = CartItem.objects.filter(id=item_id, cart__user=request.user).first()
    
    # If the item doesn't exist (already deleted), just go back to cart
    if not cart_item:
        return redirect('cart')

    product = cart_item.product
    
    # 1. Handle explicit removal
    if request.GET.get('remove') == 'true':
        cart_item.delete()
        messages.success(request, f"Removed {product.name} from your bag.")
    
    # 2. Handle Increment
    elif action == 'increment':
        if cart_item.quantity < product.quantity:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.warning(request, f"Only {product.quantity} units available.")
            
    # 3. Handle Decrement
    elif action == 'decrement':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            # If it was the last 1, delete it
            cart_item.delete()
            messages.success(request, f"Removed {product.name} from your bag.")
            
    return redirect('cart')
@login_required
def complete_purchase(request):
    with transaction.atomic():
        cart = get_object_or_404(Cart.objects.select_for_update(), user=request.user)
        cart_items = list(cart.items.select_related('product'))

        if not cart_items:
            messages.warning(request, "Your bag is empty.")
            return redirect('dashboard')

        order_total = Decimal('0.00')
        for item in cart_items:
            product = Product.objects.select_for_update().get(pk=item.product_id)
            if not product.is_available or product.quantity < item.quantity:
                messages.error(
                    request,
                    f"{product.name} no longer has enough stock. Please update your bag.",
                )
                return redirect('cart')
            order_total += product.price * item.quantity

        order = Order.objects.create(
            user=request.user,
            order_id=str(uuid.uuid4())[:12].upper(),
            total_paid=order_total,
            is_completed=True,
            payment_date=timezone.now(),
        )

        for item in cart_items:
            product = Product.objects.select_for_update().get(pk=item.product_id)
            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,
                quantity=item.quantity,
            )
            product.quantity -= item.quantity
            product.is_available = product.quantity > 0
            product.save(update_fields=['quantity', 'is_available'])

        cart.items.all().delete()

    # SEND EMAIL RECEIPT
    try:
        mail_subject = f'Order Confirmed - #{order.order_id}'
        html_message = render_to_string('emails/order_receipt.html', {
            'user': request.user,
            'order': order,
        })
        email = EmailMessage(mail_subject, html_message, to=[request.user.email])
        email.content_subtype = "html" # Main content is now text/html
        email.send()
    except Exception as e:
        print(f"Email failed: {e}")

    return render(request, 'store/success.html', {'order': order})



# --- ORDER HISTORY & INVOICE ---

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user, is_completed=True).order_by('-created_at')
    total_spent = sum(order.total_paid for order in orders)
    return render(request, 'store/order_history.html', {'orders': orders, 'total_spent': total_spent})

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'store/invoice.html', {'order': order})

@login_required
def profile_settings(request):
    if request.method == 'POST':
        user = request.user
        # Get data from the mobile-responsive form we built
        user.username = request.POST.get('username')
        user.preferred_size = request.POST.get('preferred_size')
        
        # Handle password update if provided
        new_password = request.POST.get('password')
        if new_password:
            user.set_password(new_password)
            # This keeps the user logged in after a password change
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            
        user.save()
        messages.success(request, "Settings updated successfully!")
        return redirect('profile_settings')

    return render(request, 'store/profile.html')
# --- OWNER STUDIO VIEWS ---

@user_passes_test(is_owner)
def owner_dashboard(request):
    products = Product.objects.all().order_by('-created_at')
    # Filter completed orders and take the latest 5
    orders = Order.objects.filter(is_completed=True).order_by('-created_at')[:5]
    total_sales = sum(o.total_paid for o in Order.objects.filter(is_completed=True))
    settings = StoreSettings.load()

    # Handle Store Branding Update (Sidebar Form)
    if request.method == 'POST' and 'update_settings' in request.POST:
        settings_form = StoreSettingsForm(request.POST, request.FILES, instance=settings)
        if settings_form.is_valid():
            settings_form.save()
            return redirect('owner_dashboard')
    else:
        settings_form = StoreSettingsForm(instance=settings)

    return render(request, 'store/owner_dashboard.html', {
        'products': products,
        'recent_orders': orders,
        'total_sales': total_sales,
        'settings_form': settings_form,
        'settings': settings
    })

@user_passes_test(is_owner)
@require_POST
def quick_edit_product(request):
    """Handles the high-speed modal updates from the dashboard."""
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    
    # Update price and availability directly
    product.price = request.POST.get('price')
    product.is_available = 'is_available' in request.POST
    product.save()
    
    return redirect('owner_dashboard')

@user_passes_test(is_owner)
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('owner_dashboard')
    else:
        form = ProductForm()
    return render(request, 'store/product_form.html', {'form': form, 'title': 'Add New Drop'})

@user_passes_test(is_owner)
def edit_product(request, product_id):
    """Full edit page for detailed changes."""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            return redirect('owner_dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'store/product_form.html', {'form': form, 'title': f'Edit {product.name}'})

@user_passes_test(is_owner)
def delete_product(request, product_id):
    get_object_or_404(Product, id=product_id).delete()
    return redirect('owner_dashboard')

@user_passes_test(is_owner)
def toggle_availability(request, product_id):
    """Legacy toggle logic (kept for simple table buttons)."""
    product = get_object_or_404(Product, id=product_id)
    product.is_available = not product.is_available
    product.save()
    return redirect('owner_dashboard')

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False # Deactivate account until email is verified
            user.save()
            
            # Send Verification Email
            current_site = get_current_site(request)
            mail_subject = 'Activate your Thrift Elegance Account'
            message = render_to_string('emails/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            email = EmailMessage(mail_subject, message, to=[user.email])
            email.send()
            return render(request, 'store/verify_email_sent.html')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'store/activation_success.html')
    else:
        return render(request, 'store/activation_invalid.html')
