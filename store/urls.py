# store/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('product/<slug:slug>/', views.book_detail, name='book_detail'),
    
    # Cart and Checkout Paths
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_page, name='cart_page'),
    path('update-cart/', views.update_cart_item, name='update_cart_item'),
    path('remove-cart-item/', views.remove_cart_item, name='remove_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('shipping-information/', views.shipping_info, name='shipping_info'),
    path('return-refund-policy/', views.refund_policy, name='refund_policy'),
    
    # Order Success
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),

    path('signup/', views.signup, name='signup'),
]