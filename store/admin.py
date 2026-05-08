from django.contrib import admin
from .models import Category, Book, Order

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'discount_price', 'stock', 'is_active']
    list_editable = ['price', 'discount_price', 'stock', 'is_active'] 
    list_filter = ['category', 'is_active']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)} # <--- Title type karne par slug auto-fill hoga
    
admin.site.register(Order)