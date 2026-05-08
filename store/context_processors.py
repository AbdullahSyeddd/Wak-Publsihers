# store/context_processors.py
from .models import Category, Cart # Cart import karna zaroori hai

def menu_categories(request):
    # Sirf parent categories fetch karenge, children template mein handle honge
    categories = Category.objects.filter(parent=None)
    return {'menu_categories': categories} 

def cart_processor(request):
    cart_count = 0
    cart_total = 0.00
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.get(user=request.user)
        else:
            session_key = request.session.session_key
            if session_key:
                cart = Cart.objects.get(session_id=session_key)
            else:
                cart = None
                
        if cart:
            cart_count = cart.get_cart_count
            cart_total = cart.get_cart_total
    except Cart.DoesNotExist:
        pass

    return {
        'nav_cart_count': cart_count,
        'nav_cart_total': cart_total
    }