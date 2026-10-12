from django.urls import path
from .views import (
    DashboardView,
    GoalDetailView,
    GoalListCreatView,
    ProfileView,
    TransactionDetailView,
    TransactionListCreateView,
)


urlpatterns = [
    path("auth/profile/", ProfileView.as_view(), name="profile"),
    path("transactions/", TransactionListCreateView.as_view()),
    path("transactions/<int:pk>", TransactionDetailView.as_view()),
    path("goal/", GoalListCreatView.as_view()),
    path("goal/<int:pk>/", GoalDetailView.as_view()),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
