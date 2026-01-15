from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- PUBLIC PAGES ---
    # The home/landing page of the site
    path('', views.landing_page, name='landing'),
    
    # --- AUTHENTICATION ---
    # Standard Django Login using a custom template
    path('login/', auth_views.LoginView.as_view(template_name='store/login.html'), name='login'),
    # Logout redirects user back to the landing page
    path('logout/', auth_views.LogoutView.as_view(next_page='landing'), name='logout'), 
    # Custom signup view that captures user size preferences
    path('signup/', views.personalized_signup, name='signup'),

    # --- CUSTOMER INTERFACE ---
    # Main user area showing personalized recommendations
    path('dashboard/', views.dashboard, name='dashboard'),
    # Individual product page showing details and related items
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # --- WISHLIST / FAVORITES ---
    # View to see all items the user has favorited
    path('wishlist/', views.wishlist_view, name='wishlist'),
    # Logic-only route: adds/removes item from favorites then redirects back
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),


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

    # --- OWNER / STAFF MANAGEMENT ---
    # Dashboard for staff to manage inventory
    path('management/', views.owner_dashboard, name='owner_dashboard'),
    # Completely remove a product from the database
    path('management/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    # Quickly flip a product between 'Available' and 'Sold'
    path('management/toggle/<int:product_id>/', views.toggle_availability, name='toggle_availability'),
]