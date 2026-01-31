"""
URL configuration for hotel_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    # Redirects for legacy admin-prefixed routes we provided in the app
    path('admin/notifications/', RedirectView.as_view(url='/management/notifications/', permanent=False)),
    path('admin/agent-ia/', RedirectView.as_view(url='/management/agent-ia/', permanent=False)),
    path('admin/messages/', RedirectView.as_view(url='/management/messages/', permanent=False)),

    # Django admin
    path('admin/', admin.site.urls),

    # App URLs
    path('', include('hotel.urls')),  # Inclure les URLs de l'application hotel
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
