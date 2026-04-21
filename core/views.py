from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Transaction, Goal
from .serializers import *
from django.db.models import  Sum


#registration 
class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer
    permission_classes = []


    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=201)
    

class MeView(GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

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
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)