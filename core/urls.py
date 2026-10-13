from django.urls import path
from .views import (
    BudgetDetailView,
    BudgetListCreateView,
    DashboardView,
    GoalDetailView,
    GoalListCreatView,
    ProfileView,
    ReminderDetailView,
    ReminderListCreateView,
    TransactionDetailView,
    TransactionListCreateView,
)

urlpatterns = [
    path("auth/profile/", ProfileView.as_view(), name="profile"),
    path("transactions/", TransactionListCreateView.as_view()),
    path("transactions/<int:pk>/", TransactionDetailView.as_view()),
    path("transactions/<int:pk>", TransactionDetailView.as_view()),
    path("goal/", GoalListCreatView.as_view()),
    path("goal/<int:pk>/", GoalDetailView.as_view()),
    path("goals/", GoalListCreatView.as_view()),
    path("goals/<int:pk>/", GoalDetailView.as_view()),
    path("budgets/", BudgetListCreateView.as_view(), name="budget-list"),
    path("budgets/<int:pk>/", BudgetDetailView.as_view(), name="budget-detail"),
    path("reminders/", ReminderListCreateView.as_view(), name="reminder-list"),
    path("reminders/<int:pk>/", ReminderDetailView.as_view(), name="reminder-detail"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
]
