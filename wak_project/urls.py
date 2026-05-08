# wak_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# --- ADMIN PANEL BRANDING FOR CLIENT ---
admin.site.site_header = "WAK Publishers Admin"
admin.site.site_title = "WAK Publishers Portal"
admin.site.index_title = "Welcome to WAK Bookstore Management"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('store.urls')),
    path('accounts/', include('accounts.urls')), # Ye bilkul theek jagah par hai!
]

# Images show karwane ke liye
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static('/assets/', document_root=settings.BASE_DIR / 'assets')