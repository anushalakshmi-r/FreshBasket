from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient


class PasswordResetApiTests(TestCase):
    def test_reset_confirmation_changes_password_and_request_does_not_leak_account_existence(self):
        user = get_user_model().objects.create_user(username="reset-user", email="reset@example.com", password="Old-pass-123")
        client = APIClient()
        response = client.post("/api/accounts/password-reset/", {"email": "unknown@example.com"}, format="json")
        self.assertEqual(response.status_code, 200)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        response = client.post("/api/accounts/password-reset/confirm/", {"uid": uid, "token": token, "new_password": "New-pass-123", "confirm_password": "New-pass-123"}, format="json")
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("New-pass-123"))
