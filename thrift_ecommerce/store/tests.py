from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.db.utils import OperationalError

from .models import Cart, CartItem, Order, Product, StoreSettings


class CheckoutWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="buyer@example.com",
            username="buyer",
            password="pass1234",
        )
        self.client.login(username="buyer@example.com", password="pass1234")

    def _image(self):
        return SimpleUploadedFile(
            "product.gif",
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x00\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            content_type="image/gif",
        )

    def _product(self, quantity=2):
        return Product.objects.create(
            name="Vintage Dress",
            price=Decimal("12500.00"),
            quantity=quantity,
            is_available=True,
            image=self._image(),
            size="M",
            category="DRESS",
        )

    def test_add_to_cart_stops_at_stock_limit(self):
        product = self._product(quantity=2)

        self.client.get(reverse("add_to_cart", args=[product.id]))
        self.client.get(reverse("add_to_cart", args=[product.id]))
        self.client.get(reverse("add_to_cart", args=[product.id]))

        cart_item = CartItem.objects.get(cart__user=self.user, product=product)
        self.assertEqual(cart_item.quantity, 2)

    def test_checkout_rejects_when_stock_changed(self):
        product = self._product(quantity=1)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        product.quantity = 0
        product.is_available = False
        product.save(update_fields=["quantity", "is_available"])

        response = self.client.get(reverse("complete_purchase"))

        self.assertRedirects(response, reverse("cart"))
        self.assertEqual(Order.objects.count(), 0)
        self.assertTrue(CartItem.objects.filter(cart=cart).exists())

    def test_checkout_creates_order_and_clears_cart(self):
        product = self._product(quantity=3)
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        response = self.client.get(reverse("complete_purchase"))

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total_paid, Decimal("25000.00"))
        self.assertEqual(order.items.count(), 1)

        product.refresh_from_db()
        self.assertEqual(product.quantity, 1)
        self.assertFalse(CartItem.objects.filter(cart=cart).exists())


class StoreSettingsLoadTests(TestCase):
    def test_load_returns_default_instance_when_schema_is_behind(self):
        with patch.object(StoreSettings.objects, "get_or_create", side_effect=OperationalError):
            settings_obj = StoreSettings.load()

        self.assertEqual(settings_obj.pk, 1)
        self.assertEqual(settings_obj.store_name, "ThriftElegance")
