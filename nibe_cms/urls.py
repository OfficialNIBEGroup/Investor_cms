"""
URL configuration for nibe_cms project.
"""
from functools import partial

from django.contrib import admin
from django.contrib.staticfiles.views import serve as staticfiles_serve
from django.urls import path, include, re_path
from django.conf import settings
from django.views.generic.base import RedirectView
from django.views.static import serve as media_serve

urlpatterns = [
    # Old VPS URL was https://200.97.168.12/CMS/ — send those bookmarks to domain root.
    path('CMS', RedirectView.as_view(url='/', permanent=True)),
    path('CMS/', RedirectView.as_view(url='/', permanent=True)),
    path('CMS/<path:rest>', RedirectView.as_view(url='/%(rest)s', query_string=True, permanent=True)),
    path('admin/', admin.site.urls),
    path('', include('investors.urls')),
    # Fallback if Nginx does not serve these paths itself.
    re_path(r'^static/(?P<path>.*)$', partial(staticfiles_serve, insecure=True)),
    re_path(r'^media/(?P<path>.*)$', media_serve, {'document_root': settings.MEDIA_ROOT}),
]
