"""
URL configuration for nibe_cms project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    # Old VPS URL was https://200.97.168.12/CMS/ — send those bookmarks to domain root.
    path('CMS', RedirectView.as_view(url='/', permanent=True)),
    path('CMS/', RedirectView.as_view(url='/', permanent=True)),
    path('CMS/<path:rest>', RedirectView.as_view(url='/%(rest)s', query_string=True, permanent=True)),
    path('admin/', admin.site.urls),
    path('', include('investors.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
