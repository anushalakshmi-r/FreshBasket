from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from accounts.models import CustomerAddress, CustomerProfile

User = get_user_model()


class CustomerAuthenticationTests(APITestCase):
    registration_data = {
        "first_name": "Test",
        "last_name": "Customer",
        "email": "freshbasket.auth.test@example.com",
        "phone_number": "+919876543210",
        "password": "FreshBasket-Test-2026!",
        "confirm_password": "FreshBasket-Test-2026!",
    }

    def register_customer(self):
        return self.client.post(
            "/api/accounts/register/",
            self.registration_data,
            format="json",
            secure=True,
        )

    def test_registration_creates_hashed_user_and_httponly_refresh_cookie(self):
        response = self.register_customer()

        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email=self.registration_data["email"]).exists())
        user = User.objects.get(email=self.registration_data["email"])
        self.assertTrue(user.check_password(self.registration_data["password"]))
        self.assertNotEqual(user.password, self.registration_data["password"])
        self.assertIn("access", response.data)
        self.assertNotIn("refresh", response.data)
        self.assertNotIn("password", response.data["user"])
        cookie = response.cookies[settings.AUTH_REFRESH_COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertTrue(cookie["secure"])
        self.assertEqual(cookie["samesite"], "None")
        csrf_response = self.client.get("/api/accounts/csrf/", secure=True)
        self.assertTrue(csrf_response.data["refresh_cookie_present"])

    def test_duplicate_email_is_rejected(self):
        self.assertEqual(self.register_customer().status_code, 201)
        response = self.register_customer()

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.data)
        self.assertEqual(User.objects.filter(email=self.registration_data["email"]).count(), 1)

    def test_login_accepts_email_and_rejects_invalid_password(self):
        self.register_customer()

        valid_response = self.client.post(
            "/api/accounts/login/",
            {
                "email": self.registration_data["email"],
                "password": self.registration_data["password"],
            },
            format="json",
            secure=True,
        )
        invalid_response = self.client.post(
            "/api/accounts/login/",
            {"email": self.registration_data["email"], "password": "wrong-password"},
            format="json",
            secure=True,
        )

        self.assertEqual(valid_response.status_code, 200)
        self.assertIn("access", valid_response.data)
        self.assertEqual(invalid_response.status_code, 401)

    def test_profile_requires_authentication_and_supports_get_patch(self):
        self.assertEqual(self.client.get("/api/accounts/profile/").status_code, 401)
        registration = self.register_customer()
        access = registration.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")

        get_response = self.client.get("/api/accounts/profile/")
        patch_response = self.client.patch(
            "/api/accounts/profile/",
            {
                "first_name": "Updated",
                "email": "updated.customer@example.com",
                "phone_number": "+919123456789",
            },
            format="json",
        )

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.data["first_name"], "Updated")
        self.assertEqual(patch_response.data["email"], "updated.customer@example.com")
        user = User.objects.get(email="updated.customer@example.com")
        self.assertEqual(user.first_name, "Updated")
        self.assertEqual(user.email, "updated.customer@example.com")

    def test_refresh_rotates_cookie_and_logout_blacklists_it(self):
        self.register_customer()
        cookie = self.client.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value

        refresh_response = self.client.post(
            "/api/accounts/token/refresh/",
            {},
            format="json",
            secure=True,
        )
        rotated_cookie = self.client.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value
        self.assertEqual(refresh_response.status_code, 200)
        self.assertIn("access", refresh_response.data)
        self.assertNotEqual(cookie, rotated_cookie)

        logout_response = self.client.post(
            "/api/accounts/logout/",
            {},
            format="json",
            secure=True,
        )
        self.assertEqual(logout_response.status_code, 204)
        self.assertEqual(self.client.cookies[settings.AUTH_REFRESH_COOKIE_NAME].value, "")

        self.client.cookies[settings.AUTH_REFRESH_COOKIE_NAME] = rotated_cookie
        rejected_response = self.client.post(
            "/api/accounts/token/refresh/",
            {},
            format="json",
            secure=True,
        )
        self.assertEqual(rejected_response.status_code, 401)

    def test_registration_rejects_mismatched_and_weak_passwords(self):
        mismatch_data = dict(self.registration_data, confirm_password="Different-Test-2026!")
        mismatch = self.client.post(
            "/api/accounts/register/",
            mismatch_data,
            format="json",
            secure=True,
        )
        weak_data = dict(
            self.registration_data,
            password="password",
            confirm_password="password",
        )
        weak = self.client.post(
            "/api/accounts/register/",
            weak_data,
            format="json",
            secure=True,
        )

        self.assertEqual(mismatch.status_code, 400)
        self.assertIn("confirm_password", mismatch.data)
        self.assertEqual(weak.status_code, 400)
        self.assertIn("password", weak.data)
        self.assertEqual(CustomerProfile.objects.count(), 0)

    def test_registration_requires_a_valid_csrf_token(self):
        client = APIClient(enforce_csrf_checks=True)
        csrf_headers = {"HTTP_REFERER": "https://testserver/"}
        rejected = client.post(
            "/api/accounts/register/",
            self.registration_data,
            format="json",
            secure=True,
            **csrf_headers,
        )
        csrf_response = client.get("/api/accounts/csrf/", secure=True)
        accepted = client.post(
            "/api/accounts/register/",
            self.registration_data,
            format="json",
            secure=True,
            HTTP_X_CSRFTOKEN=csrf_response.data["csrf_token"],
            **csrf_headers,
        )

        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(csrf_response.status_code, 200)
        self.assertFalse(csrf_response.data["refresh_cookie_present"])
        self.assertEqual(accepted.status_code, 201)


class CustomerAddressApiTests(APITestCase):
    address_data = {
        "full_name": "Test Customer",
        "phone_number": "+91 9876543210",
        "address_line_1": "12 Market Road",
        "address_line_2": "",
        "landmark": "Near the park",
        "city": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
        "address_type": "home",
    }

    def setUp(self):
        self.customer = User.objects.create_user(
            username="address-customer",
            email="address@example.test",
            password="test-password-only",
        )
        self.other_customer = User.objects.create_user(
            username="other-address-customer",
            email="other-address@example.test",
            password="test-password-only",
        )
        self.client.force_authenticate(user=self.customer)

    def test_create_list_and_default_address_behavior(self):
        first = self.client.post(
            "/api/accounts/addresses/",
            self.address_data,
            format="json",
        )
        second = self.client.post(
            "/api/accounts/addresses/",
            dict(self.address_data, city="Mumbai", postal_code="400001"),
            format="json",
        )

        self.assertEqual(first.status_code, 201)
        self.assertTrue(first.data["is_default"])
        self.assertEqual(first.data["phone_number"], "+919876543210")
        self.assertEqual(second.status_code, 201)
        self.assertFalse(second.data["is_default"])
        self.assertEqual(self.client.get("/api/accounts/addresses/").data[0]["id"], first.data["id"])

        set_default = self.client.post(
            f"/api/accounts/addresses/{second.data['id']}/set-default/",
            {},
            format="json",
        )
        first_address = CustomerAddress.objects.get(pk=first.data["id"])
        second_address = CustomerAddress.objects.get(pk=second.data["id"])
        self.assertEqual(set_default.status_code, 200)
        self.assertTrue(second_address.is_default)
        self.assertFalse(first_address.is_default)

        updated = self.client.patch(
            f"/api/accounts/addresses/{second.data['id']}/",
            {"is_default": False},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        first_address.refresh_from_db()
        self.assertTrue(first_address.is_default)

        deleted = self.client.delete(f"/api/accounts/addresses/{first.data['id']}/")
        self.assertEqual(deleted.status_code, 204)
        second_address.refresh_from_db()
        self.assertTrue(second_address.is_default)

    def test_address_validation_and_customer_ownership(self):
        invalid_phone = self.client.post(
            "/api/accounts/addresses/",
            dict(self.address_data, phone_number="123"),
            format="json",
        )
        invalid_postal_code = self.client.post(
            "/api/accounts/addresses/",
            dict(self.address_data, postal_code="12345"),
            format="json",
        )
        self.assertEqual(invalid_phone.status_code, 400)
        self.assertEqual(invalid_postal_code.status_code, 400)

        created = self.client.post(
            "/api/accounts/addresses/",
            self.address_data,
            format="json",
        )
        other_client = APIClient()
        other_client.force_authenticate(user=self.other_customer)
        address_url = f"/api/accounts/addresses/{created.data['id']}/"
        self.assertEqual(other_client.get(address_url).status_code, 404)
        self.assertEqual(
            other_client.patch(address_url, {"city": "Mumbai"}, format="json").status_code,
            404,
        )
        self.assertEqual(other_client.delete(address_url).status_code, 404)
