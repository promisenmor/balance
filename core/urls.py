from django.urls import path
from .views import RegisterView, MeView, TransactionDetailView, TransactionListCreateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="registration"),
    path("auth/login/", TokenObtainPairView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("auth/me/", MeView.as_view(), name="Profile"),
    path("transactions/", TransactionListCreateView.as_view()),
    path("transactions/<int:pk>", TransactionDetailView.as_view()),
]

