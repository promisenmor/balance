from .models import User, Transaction, Goal
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)


    class Meta:
        model = User
        fields = ["email", "username", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            username=validated_data["username"],
            password=validated_data["password"],

        )
        return user
    

class TransactionSerializer(serializers.ModelSerializer):
    transaction_type = serializers.CharField(source="get_transaction_type_display", read_only=True)
    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = ["user", "created_at"]



class GoalSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()
    class Meta:
        model = Goal
        fields = "__all__"
        read_only_fields = ["user", "created_at"]

    @extend_schema_field(serializers.FloatField())
    def get_progress(self, obj):
        if obj.target_amount == 0:
            return 0
        return round((obj.current_amount /obj.target_amount) * 100, 2)
    


class DashboardSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_income = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=10, decimal_places=2)
    recent_transactions = TransactionSerializer(many=True)
    goals = GoalSerializer(many=True)

    