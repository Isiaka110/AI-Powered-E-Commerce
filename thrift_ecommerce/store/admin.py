from django.contrib import admin
from .models import User, Product, Order, OrderItem

@admin.register(User)
class UserAdmin(admin.ModelAdmin): # Corrected from admin.admin.ModelAdmin
    list_display = ('email', 'username', 'preferred_size', 'is_staff')
    search_fields = ('email', 'username')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'size', 'price', 'is_available', 'created_at')
    list_filter = ('category', 'size', 'is_available')
    search_fields = ('name', 'description')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'total_paid', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'created_at')
    inlines = [OrderItemInline]