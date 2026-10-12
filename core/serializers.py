from urllib.parse import urlencode

from allauth.account.utils import user_pk_to_url_str
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from dj_rest_auth.registration.serializers import RegisterSerializer as DjRegisterSerializer
from dj_rest_auth.serializers import PasswordResetSerializer as DjPasswordResetSerializer
from rest_framework.validators import UniqueValidator

from .models import Goal, Transaction, UserProfile


class EmailRegistrationSerializer(DjRegisterSerializer):
    username = serializers.HiddenField(default="")

    def validate_username(self, username):
        if not username:
            return ""
        return super().validate_username(username)

    def validate_email(self, email):
        email = super().validate_email(email)
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with this email address already exists.")
        return email


class ApiPasswordResetSerializer(DjPasswordResetSerializer):
    def get_email_options(self):
        return {"url_generator": self.get_reset_url}

    @staticmethod
    def get_reset_url(request, user, token):
        path = reverse("rest_password_reset_confirm")
        query = urlencode(
            {
                "uid": user_pk_to_url_str(user),
                "token": token,
            }
        )
        return request.build_absolute_uri(f"{path}?{query}")


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    is_onboarded = serializers.BooleanField(read_only=True)
    phone_number = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=False,
        max_length=20,
        validators=[UniqueValidator(queryset=UserProfile.objects.all())],
    )

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "middle_name",
            "date_of_birth",
            "gender",
            "phone_number",
            "address",
            "city",
            "state",
            "country",
            "postal_code",
            "is_onboarded",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_onboarded", "created_at", "updated_at"]


class UserDetailsSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    is_email_verified = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ["id", "email", "is_email_verified", "profile"]
        read_only_fields = fields

    def get_is_email_verified(self, user):
        return user.emailaddress_set.filter(email__iexact=user.email, verified=True).exists()


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ["id", "amount", "transaction_type", "category", "created_at"]
        read_only_fields = ["id", "created_at"]


class GoalSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = [
            "id",
            "title",
            "target_amount",
            "current_amount",
            "deadline",
            "created_at",
            "progress",
        ]
        read_only_fields = ["id", "created_at", "progress"]

    @extend_schema_field(serializers.FloatField())
    def get_progress(self, obj):
        if obj.target_amount == 0:
            return 0
        return round((obj.current_amount / obj.target_amount) * 100, 2)


class DashboardSerializer(serializers.Serializer):
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_income = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_expense = serializers.DecimalField(max_digits=10, decimal_places=2)
    recent_transactions = TransactionSerializer(many=True)
    goals = GoalSerializer(many=True)
