from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- PUBLIC PAGES ---
    # The home/landing page of the site
    path('', views.landing_page, name='landing'),
    
    # --- AUTHENTICATION ---
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    # Standard Django Login using a custom template
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    # Logout redirects user back to the landing page
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'), 
    # Custom signup view that captures user size preferences
    path('signup/', views.personalized_signup, name='signup'),
    path('onboarding/', views.vendor_onboarding, name='vendor_onboarding'),
    path('terms/', views.terms_and_conditions, name='terms'),
    path('reset-password/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('settings/', views.profile_settings, name='profile_settings'),

    # --- CUSTOMER INTERFACE ---
    # Main user area showing personalized recommendations
    path('dashboard/', views.dashboard, name='dashboard'),
    # Individual product page showing details and related items
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # --- WISHLIST / FAVORITES ---
    # View to see all items the user has favorited
 # store/urls.py
    path('wishlist/', views.wishlist, name='wishlist_view'), # Added _view here
    # Logic-only route: adds/removes item from favorites then redirects back
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('product/quick-edit/', views.quick_edit_product, name='quick_edit_product'),


    path('cart/update/<int:item_id>/<str:action>/', views.update_cart_quantity, name='update_cart_quantity'),
    # --- SHOPPING CART & CHECKOUT ---
    # View the current contents of the session-based cart
    path('cart/', views.cart_view, name='cart'), 
    # Logic-only route: adds an item to the session cart
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'), 
    # Finalizes the order, clears cart, and creates database records
    path('checkout/', views.complete_purchase, name='complete_purchase'),
    # View past successful orders
    path('orders/', views.order_history, name='order_history'),
    path('order/<str:order_id>/invoice/', views.download_invoice, name='download_invoice'),
    # --- OWNER / STAFF MANAGEMENT ---
    # Dashboard for staff to manage inventory
    path('owner/dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('store-admin/', views.owner_dashboard, name='store_admin_dashboard'),
    path('owner/product/add/', views.add_product, name='add_product'),
    path('store-admin/product/add/', views.add_product, name='store_admin_add_product'),
    path('owner/product/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('management/', views.owner_dashboard, name='owner_dashboard'),
    # Completely remove a product from the database
    path('management/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    # Quickly flip a product between 'Available' and 'Sold'
    path('management/toggle/<int:product_id>/', views.toggle_availability, name='toggle_availability'),
]