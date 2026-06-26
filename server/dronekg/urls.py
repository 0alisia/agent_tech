from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/drones/', include('drones.urls')),
    path('api/forum/', include('forum.urls')),
    path('api/rag/', include('rag.urls')),
    path('api/soldering/', include('soldering.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
