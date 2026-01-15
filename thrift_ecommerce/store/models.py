from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # Use this to reference your custom User

# 1. Global Choices
SIZE_CHOICES = (
    ('XS', 'Extra Small'),
    ('S', 'Small'),
    ('M', 'Medium'),
    ('L', 'Large'),
    ('XL', 'Extra Large'),
    ('XXL', '2X Large'),
)

CATEGORY_CHOICES = (
    ('DRESS', 'Dresses'),
    ('TOP', 'Tops'),
    ('BOTTOM', 'Bottoms'),
    ('OUTER', 'Outerwear'),
    ('ACC', 'Accessories'),
)

# 2. Custom User Model
class User(AbstractUser):
    email = models.EmailField(unique=True) 
    preferred_size = models.CharField(
        max_length=5, 
        choices=SIZE_CHOICES, 
        blank=True, 
        null=True,
        help_text="Used by AI to curate your personalized rack"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

# 3. Product Model
class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Detailed info for the Product Page")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='products/') 
    size = models.CharField(max_length=5, choices=SIZE_CHOICES)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='DRESS')
    is_available = models.BooleanField(default=True)
    favorites = models.ManyToManyField(User, related_name="favorites", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.size})"

    @property
    def current_price(self):
        if self.discount_price:
            return self.discount_price
        return self.price

# --- NEW MODELS ADDED BELOW ---

# 4. Cart Model
class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart: {self.user.email}"

    @property
    def total_price(self):
        return sum(item.get_total for item in self.items.all())

# 5. Cart Item Model (This fixes your ImportError)
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def get_total(self):
        return self.product.current_price * self.quantity

# --- EXISTING ORDER MODELS ---

# 6. Order Model
class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2)
    order_id = models.CharField(max_length=100, unique=True)
    is_completed = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.order_id} by {self.user.email}"

# 7. Order Item Model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Deleted Item'}"

    @property
    def get_total(self):
        return self.price * self.quantity