from django.shortcuts import render
from rest_framework.generics import (
    GenericAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
    RetrieveUpdateAPIView,
)
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from dj_rest_auth.views import PasswordResetConfirmView as DjPasswordResetConfirmView

from .models import Budget, Goal, Reminder, Transaction, UserProfile
from .serializers import (
    BudgetSerializer,
    DashboardSerializer,
    GoalSerializer,
    ProfileSerializer,
    ReminderSerializer,
    TransactionSerializer,
)


class PasswordResetConfirmPageView(DjPasswordResetConfirmView):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            "core/password_reset_confirm.html",
            {
                "uid": request.query_params.get("uid", ""),
                "token": request.query_params.get("token", ""),
            },
        )


class ProfileView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

#List and create
class TransactionListCreateView(ListCreateAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        

# retrieve, update and delete
class TransactionDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class GoalListCreatView(ListCreateAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GoalDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)


class BudgetListCreateView(ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class BudgetDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


class ReminderListCreateView(ListCreateAPIView):
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReminderDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ReminderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Reminder.objects.filter(user=self.request.user)


# Dashboard view
class DashboardView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DashboardSerializer

    def get(self, request):
        user = request.user

        transactions = Transaction.objects.filter(user=user)

        total_income = transactions.filter(
            transaction_type="income"
        ).aggregate(total=Sum("amount"))["total"] or 0

        total_expense = transactions.filter(
            transaction_type="expense"
        ).aggregate(total=Sum("amount"))["total"] or 0


        balance = total_income - total_expense

        data = {
            "balance": balance,
            "total_income" : total_income,
            "total_expense" : total_expense,
            "recent_transactions": transactions.order_by("-created_at")[:5],
            "goals": Goal.objects.filter(user=user).order_by("-created_at")[:5],
            "budgets": user.budgets.all(),
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)