from urllib.parse import urlencode

from allauth.account.utils import user_pk_to_url_str
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from dj_rest_auth.registration.serializers import RegisterSerializer as DjRegisterSerializer
from dj_rest_auth.serializers import PasswordResetSerializer as DjPasswordResetSerializer
from rest_framework.validators import UniqueValidator

from .models import Budget, Goal, Reminder, Transaction, UserProfile
from .services import get_budget_status


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
        fields = [
            "id",
            "amount",
            "transaction_type",
            "category",
            "transaction_date",
            "description",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_category(self, value):
        category = value.strip()
        if not category:
            raise serializers.ValidationError("Category cannot be blank.")
        return category.casefold()


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
    budgets = serializers.SerializerMethodField()

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_budgets(self, data):
        return BudgetSerializer(
            data["budgets"],
            many=True,
            context=self.context,
        ).data


class BudgetSerializer(serializers.ModelSerializer):
    spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    remaining = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    percent_used = serializers.DecimalField(max_digits=7, decimal_places=2, read_only=True)
    alert_level = serializers.ChoiceField(
        choices=("none", "warning", "exceeded"),
        read_only=True,
    )
    period_start = serializers.DateField(read_only=True)
    period_end = serializers.DateField(read_only=True)

    class Meta:
        model = Budget
        fields = [
            "id",
            "category",
            "limit_amount",
            "period",
            "spent",
            "remaining",
            "percent_used",
            "alert_level",
            "period_start",
            "period_end",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "spent",
            "remaining",
            "percent_used",
            "alert_level",
            "period_start",
            "period_end",
            "created_at",
            "updated_at",
        ]

    def validate_category(self, value):
        category = value.strip()
        if not category:
            raise serializers.ValidationError("Category cannot be blank.")
        return category.casefold()

    def validate(self, attrs):
        user = self.context["request"].user
        category = attrs.get("category", getattr(self.instance, "category", ""))
        period = attrs.get("period", getattr(self.instance, "period", Budget.Period.MONTHLY))
        duplicate_budgets = Budget.objects.filter(
            user=user,
            category__iexact=category,
            period=period,
        )
        if self.instance:
            duplicate_budgets = duplicate_budgets.exclude(pk=self.instance.pk)
        if duplicate_budgets.exists():
            raise serializers.ValidationError(
                {"category": "A budget for this category and period already exists."}
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        status = get_budget_status(instance)
        data.update(
            {
                "spent": status["spent"],
                "remaining": status["remaining"],
                "percent_used": status["percent_used"],
                "alert_level": status["alert_level"],
                "period_start": status["period_start"],
                "period_end": status["period_end"],
            }
        )
        return data


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        fields = [
            "id",
            "title",
            "message",
            "remind_at",
            "is_completed",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
