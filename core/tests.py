import re
from urllib.parse import parse_qs, urlparse

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.test import TestCase, override_settings
from allauth.account.models import EmailAddress, EmailConfirmationHMAC
from rest_framework.test import APIClient

from .models import UserProfile


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
