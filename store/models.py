from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify # <--- Naya import slug ke liye

# --- CATEGORY MODEL ---
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', related_name='children', on_delete=models.CASCADE, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        full_path = [self.name]
        k = self.parent
        visited = {self.id}  # SAFEGUARD: Hum check karenge ke konsi category visit ho chuki hai
        
        while k is not None:
            if k.id in visited:
                # Agar ghalti se loop ban gaya hai (circular relation), toh break kar do
                full_path.append("[]")
                break
            
            full_path.append(k.name)
            visited.add(k.id)
            k = k.parent
            
        return ' -> '.join(full_path[::-1])

# --- BOOK MODEL ---
class Book(models.Model):
    category = models.ForeignKey(Category, related_name='books', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, null=True) # <--- Naya field product detail page ke liye
    author = models.CharField(max_length=200, default="WAK Publishers")
    
    # Description ab optional hai
    description = models.TextField(blank=True, null=True) 
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # --- DUAL IMAGE SYSTEM ---
    image = models.CharField(max_length=500, blank=True, null=True, help_text="Paste URL or /assets/ path") 
    cover_image = models.ImageField(upload_to='book_covers/', blank=True, null=True, help_text="OR Upload file from computer")
    
    stock = models.PositiveIntegerField(default=10) # Default 10 books ka stock set kar diya hai
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug if not provided
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    @property
    def get_image(self):
        # Image fetch logic: File ko priority deta hai, warna URL/Text, warna default logo
        if self.cover_image:
            return self.cover_image.url
        elif self.image:
            return self.image
        return '/assets/WAK-LOGO.png'

    def __str__(self):
        return self.title

# --- CART & ORDER MODELS ---
class Cart(models.Model):
    # User optional ho gaya
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    # Guest checkout ke liye Session ID
    session_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # --- NAYI PROPERTIES ---
    @property
    def get_cart_total(self):
        cart_items = self.items.all()
        return sum((item.book.discount_price if item.book.discount_price else item.book.price) * item.quantity for item in cart_items)

    @property
    def get_cart_count(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class Order(models.Model):
    # User optional ho gaya
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    shipping_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Easypaisa')
    
    sender_number = models.CharField(max_length=20, blank=True, null=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Order {self.id} - {self.user.username}"
        return f"Order {self.id} - {self.full_name} (Guest)"