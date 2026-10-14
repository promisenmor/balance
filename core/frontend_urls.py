from django.urls import path

from . import views


urlpatterns = [
    path("login/", views.frontend_login, name="frontend-login"),
    path("register/", views.frontend_register, name="frontend-register"),
    path("logout/", views.frontend_logout, name="frontend-logout"),
    path("", views.frontend_dashboard, name="frontend-dashboard"),
    path("transactions/", views.frontend_transactions, name="frontend-transactions"),
    path("budgets/", views.frontend_budgets, name="frontend-budgets"),
    path("goals/", views.frontend_goals, name="frontend-goals"),
    path("analytics/", views.frontend_analytics, name="frontend-analytics"),
    path("settings/", views.frontend_settings, name="frontend-settings"),
]
