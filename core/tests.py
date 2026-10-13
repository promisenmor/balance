from datetime import date, timedelta
from decimal import Decimal
import re
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from rest_framework.test import APIClient

from .models import Budget, Goal, Reminder, Transaction, UserProfile
from .services import get_budget_period


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AuthenticationFlowTests(TestCase):
    password = "C0balt!Orbit-9273"

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def register(self, email="user@example.com", password=None):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(
                "/api/auth/registration/",
                {
                    "email": email,
                    "password1": password or self.password,
                    "password2": password or self.password,
                },
                format="json",
            )

    def verify_email(self, email):
        email_address = EmailAddress.objects.get(user__email=email)
        confirmation = EmailConfirmationHMAC(email_address)
        confirmation_page = self.client.get(
            f"/api/auth/registration/account-confirm-email/{confirmation.key}/"
        )
        self.assertEqual(confirmation_page.status_code, 200)
        self.assertFalse(email_address.verified)
        return self.client.post(
            "/api/auth/registration/verify-email/",
            {"key": confirmation.key},
            format="json",
        )

    def login(self, email="user@example.com", password=None):
        return self.client.post(
            "/api/auth/login/",
            {"email": email, "password": password or self.password},
            format="json",
        )

    def test_registration_creates_hashed_user_profile_and_sends_verification(self):
        response = self.register()

        self.assertEqual(response.status_code, 201, response.data)
        user = get_user_model().objects.get(email="user@example.com")
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())
        self.assertFalse(EmailAddress.objects.get(user=user).verified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertNotIn("access", response.data)

    def test_duplicate_email_and_weak_password_are_rejected(self):
        self.assertEqual(self.register().status_code, 201)
        duplicate_response = self.register(email="USER@example.com")
        weak_response = self.register(
            email="another@example.com",
            password="password",
        )

        self.assertEqual(duplicate_response.status_code, 400)
        self.assertEqual(weak_response.status_code, 400)
        self.assertEqual(get_user_model().objects.filter(email__iexact="user@example.com").count(), 1)
        self.assertFalse(get_user_model().objects.filter(email="another@example.com").exists())

    def test_email_verification_enables_login_and_profile_completion(self):
        self.assertEqual(self.register().status_code, 201)
        unverified_login = self.login()
        self.assertEqual(unverified_login.status_code, 400)

        invalid_verification = self.client.post(
            "/api/auth/registration/verify-email/",
            {"key": "not-a-valid-key"},
            format="json",
        )
        self.assertEqual(invalid_verification.status_code, 404)

        verification = self.verify_email("user@example.com")
        self.assertEqual(verification.status_code, 200, verification.data)
        self.assertEqual(self.login(password="Incorrect!Password-8473").status_code, 400)
        login_response = self.login()
        self.assertEqual(login_response.status_code, 200, login_response.data)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        user_response = self.client.get("/api/auth/user/")
        self.assertEqual(user_response.status_code, 200)
        self.assertTrue(user_response.data["is_email_verified"])
        self.assertFalse(user_response.data["profile"]["is_onboarded"])
        self.assertNotIn("bvn", user_response.data["profile"])
        self.assertNotIn("pin", user_response.data["profile"])

        profile_response = self.client.patch(
            "/api/auth/profile/",
            {"first_name": "Ada", "last_name": "Okafor"},
            format="json",
        )
        self.assertEqual(profile_response.status_code, 200, profile_response.data)
        self.assertTrue(profile_response.data["is_onboarded"])
        self.assertEqual(profile_response.data["email"], "user@example.com")

    def test_profile_requires_authentication(self):
        response = self.client.get("/api/auth/profile/")
        self.assertEqual(response.status_code, 401)

    def test_registered_user_can_log_in_with_a_session(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.verify_email("user@example.com").status_code, 200)

        response = self.client.post(
            "/api-auth/login/",
            {"username": "user@example.com", "password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/api/transactions/").status_code, 200)

    def test_password_change_and_reset(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.verify_email("user@example.com").status_code, 200)
        login_response = self.login()
        self.assertEqual(login_response.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        changed_password = "New!Password-5729"
        change_response = self.client.post(
            "/api/auth/password/change/",
            {
                "old_password": self.password,
                "new_password1": changed_password,
                "new_password2": changed_password,
            },
            format="json",
        )
        self.assertEqual(change_response.status_code, 200, change_response.data)
        self.client.credentials()
        self.assertEqual(self.login(password=self.password).status_code, 400)
        self.assertEqual(self.login(password=changed_password).status_code, 200)

        reset_response = self.client.post(
            "/api/auth/password/reset/",
            {"email": "user@example.com"},
            format="json",
        )
        self.assertEqual(reset_response.status_code, 200, reset_response.data)
        self.assertEqual(len(mail.outbox), 2)

        reset_password = "Reset!Password-5821"
        reset_url = re.search(
            r"https?://[^\s<>\"']+",
            mail.outbox[-1].body,
        ).group(0).rstrip(").")
        reset_query = parse_qs(urlparse(reset_url).query)
        reset_page = self.client.get(reset_url)
        self.assertEqual(reset_page.status_code, 200, reset_url)
        self.assertContains(reset_page, "Choose a new password")
        reset_confirm_response = self.client.post(
            "/api/auth/password/reset/confirm/",
            {
                "uid": reset_query["uid"][0],
                "token": reset_query["token"][0],
                "new_password1": reset_password,
                "new_password2": reset_password,
            },
            format="json",
        )
        self.assertEqual(
            reset_confirm_response.status_code,
            200,
            reset_confirm_response.data,
        )
        self.assertEqual(self.login(password=reset_password).status_code, 200)

    def test_logout_blacklists_refresh_token(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.verify_email("user@example.com").status_code, 200)
        login_response = self.login()
        self.assertEqual(login_response.status_code, 200)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}"
        )

        logout_response = self.client.post(
            "/api/auth/logout/",
            {"refresh": login_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(logout_response.status_code, 200, logout_response.data)
        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": login_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, 401)


class CoreApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="owner",
            email="owner@example.com",
            password="Strong-password-9274",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other",
            email="other@example.com",
            password="Strong-password-9274",
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_transaction_validation_and_budget_alerts(self):
        budget_response = self.client.post(
            "/api/budgets/",
            {"category": " Food ", "limit_amount": "100.00"},
            format="json",
        )
        self.assertEqual(budget_response.status_code, 201, budget_response.data)
        self.assertEqual(budget_response.data["category"], "food")

        transaction_response = self.client.post(
            "/api/transactions/",
            {
                "amount": "79.99",
                "transaction_type": "expense",
                "category": " FOOD ",
                "description": "Groceries",
            },
            format="json",
        )
        self.assertEqual(transaction_response.status_code, 201, transaction_response.data)
        self.assertEqual(transaction_response.data["category"], "food")
        legacy_detail = self.client.get(
            f"/api/transactions/{transaction_response.data['id']}"
        )
        self.assertEqual(legacy_detail.status_code, 200)

        budget_response = self.client.get("/api/budgets/")
        self.assertEqual(budget_response.data[0]["alert_level"], "none")
        self.assertEqual(budget_response.data[0]["remaining"], Decimal("20.01"))

        warning_transaction = self.client.post(
            "/api/transactions/",
            {
                "amount": "0.01",
                "transaction_type": "expense",
                "category": "food",
            },
            format="json",
        )
        self.assertEqual(warning_transaction.status_code, 201)
        budget_response = self.client.get("/api/budgets/")
        self.assertEqual(budget_response.data[0]["alert_level"], "warning")
        self.assertEqual(budget_response.data[0]["percent_used"], Decimal("80.00"))

        over_limit_transaction = self.client.post(
            "/api/transactions/",
            {
                "amount": "25.00",
                "transaction_type": "expense",
                "category": "food",
            },
            format="json",
        )
        self.assertEqual(over_limit_transaction.status_code, 201)
        budget_response = self.client.get("/api/budgets/")
        self.assertEqual(budget_response.data[0]["alert_level"], "exceeded")
        self.assertEqual(budget_response.data[0]["remaining"], Decimal("-5"))

        invalid_transaction = self.client.post(
            "/api/transactions/",
            {
                "amount": "0",
                "transaction_type": "expense",
                "category": "food",
            },
            format="json",
        )
        self.assertEqual(invalid_transaction.status_code, 400)

    def test_budget_period_boundaries_and_user_isolation(self):
        budget = Budget.objects.create(
            user=self.user,
            category="food",
            limit_amount="100.00",
            period=Budget.Period.MONTHLY,
        )
        Transaction.objects.create(
            user=self.user,
            amount="15.00",
            transaction_type="expense",
            category="food",
            transaction_date=timezone.localdate().replace(day=1) - timedelta(days=1),
        )
        Transaction.objects.create(
            user=self.user,
            amount="30.00",
            transaction_type="expense",
            category="food",
            transaction_date=timezone.localdate().replace(day=1),
        )
        Transaction.objects.create(
            user=self.other_user,
            amount="40.00",
            transaction_type="expense",
            category="food",
            transaction_date=timezone.localdate().replace(day=2),
        )
        response = self.client.get("/api/budgets/")
        period_start, period_end = get_budget_period(
            Budget.Period.MONTHLY,
            timezone.localdate(),
        )
        self.assertEqual(response.data[0]["spent"], Decimal("30"))
        self.assertEqual(response.data[0]["period_start"], period_start)
        self.assertEqual(
            response.data[0]["period_end"],
            period_end - timedelta(days=1),
        )
        self.assertEqual(self.client.get(f"/api/budgets/{budget.pk}/").status_code, 200)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.get(f"/api/budgets/{budget.pk}/").status_code, 404)

        self.assertEqual(
            get_budget_period(Budget.Period.WEEKLY, date(2026, 10, 14)),
            (date(2026, 10, 12), date(2026, 10, 19)),
        )
        self.assertEqual(
            get_budget_period(Budget.Period.YEARLY, date(2026, 10, 14)),
            (date(2026, 1, 1), date(2027, 1, 1)),
        )

    def test_goals_reminders_and_dashboard(self):
        goal_response = self.client.post(
            "/api/goals/",
            {
                "title": "Emergency fund",
                "target_amount": "1000.00",
                "current_amount": "100.00",
            },
            format="json",
        )
        self.assertEqual(goal_response.status_code, 201, goal_response.data)
        self.assertEqual(goal_response.data["progress"], 10.0)

        invalid_goal = self.client.post(
            "/api/goals/",
            {"title": "Invalid", "target_amount": "0"},
            format="json",
        )
        self.assertEqual(invalid_goal.status_code, 400)

        reminder_response = self.client.post(
            "/api/reminders/",
            {
                "title": "Review spending",
                "message": "Check this month's expenses.",
                "remind_at": (timezone.now() + timedelta(days=1)).isoformat(),
            },
            format="json",
        )
        self.assertEqual(reminder_response.status_code, 201, reminder_response.data)
        reminder = Reminder.objects.get(pk=reminder_response.data["id"])
        self.assertEqual(reminder.user, self.user)
        self.assertEqual(self.client.patch(
            f"/api/reminders/{reminder.pk}/",
            {"is_completed": True},
            format="json",
        ).status_code, 200)
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.get(f"/api/reminders/{reminder.pk}/").status_code, 404)

        self.client.force_authenticate(self.user)
        dashboard = self.client.get("/api/dashboard/")
        self.assertEqual(dashboard.status_code, 200, dashboard.data)
        self.assertIn("budgets", dashboard.data)
        self.assertEqual(dashboard.data["goals"][0]["title"], "Emergency fund")

    def test_session_authentication_is_enabled_for_api(self):
        self.client.force_authenticate(user=None)
        self.assertTrue(self.client.login(username="owner", password="Strong-password-9274"))
        response = self.client.get("/api/transactions/")
        self.assertEqual(response.status_code, 200, response.data)
