from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

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
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
