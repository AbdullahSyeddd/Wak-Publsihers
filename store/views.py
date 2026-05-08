from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Category, Book, Cart, CartItem, Order
import json

# FOR EMAIL NOTIFICATION
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
# store/views.py ke TOP par add karein:
from django.contrib.auth import login
from .forms import CustomerSignUpForm

def home(request):
    books = Book.objects.all()
    categories = Category.objects.filter(parent__isnull=True) 

    # 1. Search Logic
    query = request.GET.get('q')
    if query:
        books = books.filter(title__icontains=query)

    # 2. Category Filter Logic (SMART LOGIC)
    cat_id = request.GET.get('category')
    if cat_id:
        try:
            selected_category = Category.objects.get(id=cat_id)
            categories_to_include = [selected_category] + list(selected_category.children.all())
            books = books.filter(category__in=categories_to_include)
        except Category.DoesNotExist:
            pass

    # 3. Sorting Logic (Low to High / High to Low)
    sort_by = request.GET.get('sort')
    if sort_by == 'price_low':
        books = books.order_by('price')
    elif sort_by == 'price_high':
        books = books.order_by('-price')
    else:
        books = books.order_by('-created_at') # Default sorting

    context = {
        'books': books,
        'categories': categories
    }
    return render(request, 'store/home.html', context)

def book_detail(request, slug):
    book = get_object_or_404(Book, slug=slug)
    return render(request, 'store/book_detail.html', {'book': book})

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    categories_to_include = [category] + list(category.children.all())
    books = Book.objects.filter(category__in=categories_to_include)
    return render(request, 'store/category.html', {'category': category, 'books': books})

# ==========================================================
# SMART CART HELPER (Login aur Guest dono ko handle karega)
# ==========================================================
def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(session_id=request.session.session_key)
    return cart

# ==========================================================

def add_to_cart(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        book_id = data.get('book_id')
        book = get_object_or_404(Book, id=book_id)
        
        # --- SECURITY CHECK: Stock check karna ---
        if book.stock <= 0:
            return JsonResponse({'status': 'error', 'message': 'Sorry, this book is out of stock!'})
        
        # Smart Helper use kiya hai
        cart = _get_or_create_cart(request)
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, book=book)
        
        if not item_created:
            cart_item.quantity += 1
            cart_item.save()
            
        # --- VIP LIVE DATA RETURNING ---
        return JsonResponse({
            'status': 'success', 
            'message': f'"{book.title}" added to cart successfully!',
            'cart_count': cart.get_cart_count,
            'cart_total': cart.get_cart_total
        })
            
    return JsonResponse({'status': 'invalid request'}, status=400)

def cart_page(request):
    cart = _get_or_create_cart(request)
    cart_items = cart.items.all()
    subtotal = sum((item.book.discount_price if item.book.discount_price else item.book.price) * item.quantity for item in cart_items)
    shipping = 150 if subtotal > 0 else 0
    total_amount = subtotal + shipping
    
    context = {'cart_items': cart_items, 'subtotal': subtotal, 'shipping': shipping, 'total_amount': total_amount}
    return render(request, 'store/cart.html', context)


def checkout(request):
    cart = _get_or_create_cart(request)
    cart_items = cart.items.all()
    
    if not cart_items.exists():
        return redirect('cart_page')
        
    subtotal = sum((item.book.discount_price if item.book.discount_price else item.book.price) * item.quantity for item in cart_items)
    shipping = 150
    total_amount = subtotal + shipping

    error_message = None # Naya variable error show karne ke liye

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method')
        sender_number = request.POST.get('sender_number')
        transaction_id = request.POST.get('transaction_id')
        
        # ========================================================
        # SECURITY CHECK: Duplicate Transaction ID
        # ========================================================

        if transaction_id and Order.objects.filter(transaction_id=transaction_id).exists():
            error_message = "Fraud Alert: This Transaction ID has already been used! Please enter a valid, new TID."
            
            # Form ko wapis render karein error message ke sath
            context = {'cart_items': cart_items, 'subtotal': subtotal, 'shipping': shipping, 'total_amount': total_amount, 'error_message': error_message}
            return render(request, 'store/checkout.html', context)
        
        # ========================================================

        # Agar TID fresh hai toh Order Save Karein
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            phone_number=phone_number,
            shipping_address=address,
            total_amount=total_amount,
            payment_method=payment_method,
            sender_number=sender_number,
            transaction_id=transaction_id
        )

        # EMAIL NOTIFICATION LOGIC (VIP HTML RECEIPT)
        try:
            html_content = render_to_string('store/email_receipt.html', {
                'order': order, 'cart_items': cart_items, 'subtotal': subtotal, 'shipping': shipping
            })
            text_content = strip_tags(html_content)

            subject = f"Order Confirmation - WAK Publishers (Order #{order.id})"
            from_email = settings.EMAIL_HOST_USER
            to_emails = ['abdullahsyed2326@gmail.com'] # ----- RECEIVER ADMIN MAIL -------- 
            if request.user.is_authenticated and request.user.email:
                to_emails.append(request.user.email)

            msg = EmailMultiAlternatives(subject, text_content, from_email, to_emails)
            msg.attach_alternative(html_content, "text/html") 
            msg.send(fail_silently=False)
        except Exception as e:
            print(f"Email failed to send: {e}")

        cart_items.delete() 
        return redirect('order_success', order_id=order.id)

    context = {'cart_items': cart_items, 'subtotal': subtotal, 'shipping': shipping, 'total_amount': total_amount, 'error_message': error_message}
    return render(request, 'store/checkout.html', context)

def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/order_success.html', {'order': order})

def update_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        action = data.get('action')
        
        try:
            cart = _get_or_create_cart(request)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            
            # Stock aur quantity update check
            if action == 'increase':
                if cart_item.book.stock > cart_item.quantity:
                    cart_item.quantity += 1
                    cart_item.save()
                else:
                    return JsonResponse({'status': 'error', 'message': 'Not enough stock available!'})
            elif action == 'decrease' and cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                
            # Item ka apna total
            price = cart_item.book.discount_price if cart_item.book.discount_price else cart_item.book.price
            item_subtotal = price * cart_item.quantity
            
            # Pure Cart ka total
            cart_items = cart.items.all()
            subtotal = sum((item.book.discount_price if item.book.discount_price else item.book.price) * item.quantity for item in cart_items)
            shipping = 150 if subtotal > 0 else 0
            
            return JsonResponse({
                'status': 'success',
                'quantity': cart_item.quantity,
                'item_subtotal': item_subtotal,
                'subtotal': subtotal,
                'shipping': shipping,
                'total_amount': subtotal + shipping,
                'cart_count': cart.get_cart_count,
                'cart_total': cart.get_cart_total
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found in cart.'})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

def remove_cart_item(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        item_id = data.get('item_id')
        
        try:
            cart = _get_or_create_cart(request)
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete() # Item Database se delete ho gaya!
            
            # Naya total calculate karo
            cart_items = cart.items.all()
            
            # Total quantity nikali hai taake navbar count sahi rahay
            cart_count = sum(item.quantity for item in cart_items) 
            subtotal = sum((item.book.discount_price if item.book.discount_price else item.book.price) * item.quantity for item in cart_items)
            shipping = 150 if subtotal > 0 else 0
            
            return JsonResponse({
                'status': 'success',
                'subtotal': subtotal,
                'shipping': shipping,
                'total_amount': subtotal + shipping,
                'cart_count': cart_count
            })
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Item not found.'})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})


def signup(request):
    if request.user.is_authenticated:
        return redirect('home') # Agar pehle se login hai toh wapis bhej do
        
    if request.method == 'POST':
        form = CustomerSignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # ==========================================
            # SECURITY: Admin access hamesha ke liye block
            # ==========================================
            user.is_staff = False 
            user.is_superuser = False
            user.save()
            
            # Account banne ke foran baad automatically login karwa do
            login(request, user)
            return redirect('home')
    else:
        form = CustomerSignUpForm()
        
    return render(request, 'accounts/signup.html', {'form': form})

def shipping_info(request):
    return render(request, 'store/shipping_info.html')

def refund_policy(request):
    return render(request, 'store/refund_policy.html')