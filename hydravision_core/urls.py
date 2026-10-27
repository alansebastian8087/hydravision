from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import common_home

urlpatterns = [
    path('', common_home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('customers/', include('customers.urls')),
    path('samples/', include('samples.urls')),
    path('reports/', include('reports.urls')),
    path('payments/', include('payments.urls')),
    path('dashboard/', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)