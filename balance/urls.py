"""
URL configuration for balance project.

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
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.views import PasswordResetConfirmPageView


urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("core.frontend_urls")),
    path("api-auth/", include("rest_framework.urls")),
    re_path(
        r'^api/auth/password/reset/confirm/?$',
        PasswordResetConfirmPageView.as_view(),
        name='password_reset_confirm_page',
    ),
    path('api/auth/', include('dj_rest_auth.urls')),
    path(
        'api/auth/registration/account-confirm-email/<str:key>/',
        TemplateView.as_view(template_name='core/email_confirm.html'),
        name='account_confirm_email',
    ),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path("api/", include("core.urls")),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(), name='swagger-ui'),
]
