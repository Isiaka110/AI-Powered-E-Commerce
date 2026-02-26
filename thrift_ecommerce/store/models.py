from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.text import slugify
from django.db.utils import OperationalError, ProgrammingError

# --- EDITABLE CONFIGURATION ---
# To add/remove sizes, simply update these lists.
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

# --- 1. STORE BRANDING MODEL ---
class StoreSettings(models.Model):
    """Global settings for the platform owner to manage branding."""
    store_name = models.CharField(max_length=100, default="ThriftElegance")
    logo = models.ImageField(upload_to='store_assets/', blank=True, null=True)
    allow_pickup = models.BooleanField(default=True)
    allow_waybill_delivery = models.BooleanField(default=True)
    pre_purchase_instruction = models.TextField(blank=True)
    RECEIPT_CHANNEL_CHOICES = (
        ('EMAIL', 'Email receipt'),
        ('DM', 'Send receipt to direct message'),
        ('SOCIAL_INBOX', 'Send receipt to social inbox'),
        ('NONE', 'Do not send a receipt automatically'),
    )
    receipt_channel = models.CharField(max_length=20, choices=RECEIPT_CHANNEL_CHOICES, default='EMAIL')
    owner_whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        help_text="Use international format, e.g. 2348012345678 (no + or spaces).",
    )
    whatsapp_message_template = models.TextField(
        blank=True,
        default="Hi {{store_name}}, I just completed order #{{order_id}} for ₦{{total_paid}}.",
        help_text="Template supports: {{store_name}}, {{order_id}}, {{total_paid}}, {{fulfillment_method}}, {{logistics_note}}, {{item_summary}}",
    )
    auto_open_whatsapp_on_checkout = models.BooleanField(
        default=True,
        help_text="Automatically open WhatsApp with order details after successful checkout.",
    )
    
    class Meta:
        verbose_name_plural = "Store Settings"

    def __str__(self):
        return self.store_name

    @classmethod
    def load(cls):
        """Load the singleton settings row.

        When the local database schema is behind the current model state
        (for example, before running pending migrations), querying all model
        columns can raise OperationalError/ProgrammingError. In that case,
        return an in-memory default instance so templates can still render
        while migrations are being applied.
        """
        try:
            obj, created = cls.objects.get_or_create(pk=1)
        except (OperationalError, ProgrammingError):
            return cls(pk=1)
        return obj

# --- 2. CUSTOM USER MODEL ---
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


class VendorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='vendor_profile')
    business_name = models.CharField(max_length=120)
    contact_phone = models.CharField(max_length=30)
    storefront_slug = models.SlugField(unique=True, max_length=140, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} ({self.user.email})"

    def save(self, *args, **kwargs):
        if not self.storefront_slug:
            base_slug = slugify(self.business_name) or slugify(self.user.username) or f"vendor-{self.user_id}"
            slug = base_slug
            counter = 1
            while VendorProfile.objects.filter(storefront_slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.storefront_slug = slug
        super().save(*args, **kwargs)

# --- 3. PRODUCT MODEL ---
class Product(models.Model):
    # Core Info
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Detailed info for the Product Page")
    
    # Pricing (Support larger Naira values)
    price = models.DecimalField(max_digits=12, decimal_places=2, help_text="The current selling price")
    original_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Slashed price (e.g., 50000)")
    
    # Inventory
    quantity = models.PositiveIntegerField(default=1, help_text="How many units are in stock")
    is_available = models.BooleanField(default=True)
    
    # Media
    image = models.ImageField(upload_to='products/', help_text="Primary display image") 
    image_hover = models.ImageField(upload_to='products/', blank=True, null=True, help_text="Secondary/Detail image")
    
    # Attributes
    size = models.CharField(max_length=10, choices=SIZE_CHOICES) # Increased max_length for safety
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='DRESS')
    
    # Meta
    favorites = models.ManyToManyField(User, related_name="favorites", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.size})"

    @property
    def on_sale(self):
        """Returns True if there is a slashed price higher than the current price."""
        return self.original_price is not None and self.original_price > self.price

    @property
    def is_out_of_stock(self):
        """Helper to check stock levels."""
        return self.quantity == 0

    def save(self, *args, **kwargs):
        """Auto-disable availability if quantity hits zero."""
        if self.quantity == 0:
            self.is_available = False
        super().save(*args, **kwargs)


class PromoCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    discount_percentage = models.PositiveIntegerField(help_text="e.g., 10 for 10% off")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} (-{self.discount_percentage}%)"

class SiteBanner(models.Model):
    text = models.CharField(max_length=255, help_text="Announcement text")
    sub_text = models.CharField(max_length=255, blank=True)
    is_visible = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

# --- 4. CART & ITEMS ---
class Cart(models.Model):
    FULFILLMENT_CHOICES = (
        ('PICKUP', 'Pickup'),
        ('WAYBILL', 'Waybill delivery'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    fulfillment_method = models.CharField(max_length=10, choices=FULFILLMENT_CHOICES, default='PICKUP')
    logistics_note = models.CharField(max_length=255, blank=True)

    @property
    def total_price(self):
        return sum(item.get_total for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    @property
    def get_total(self):
        return self.product.price * self.quantity

# --- 5. ORDER & ITEMS ---
class Order(models.Model):
    FULFILLMENT_CHOICES = (
        ('PICKUP', 'Pickup'),
        ('WAYBILL', 'Waybill delivery'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2)
    order_id = models.CharField(max_length=100, unique=True)
    is_completed = models.BooleanField(default=False)
    payment_date = models.DateTimeField(null=True, blank=True)
    fulfillment_method = models.CharField(max_length=10, choices=FULFILLMENT_CHOICES, default='PICKUP')
    logistics_note = models.CharField(max_length=255, blank=True)
    receipt_channel_used = models.CharField(max_length=20, default='EMAIL')
    pre_purchase_instruction_snapshot = models.TextField(blank=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
