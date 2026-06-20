# =============================================================================
# === backend/apps/authentication/tests.py ===
# =============================================================================
"""
DevelopIndo — Authentication Flow Tests

Covers every endpoint in apps/authentication/views.py:
  POST /api/auth/register/
  POST /api/auth/login/
  POST /api/auth/refresh/
  POST /api/auth/logout/
  GET  /api/auth/me/
  PUT  /api/auth/me/

Each class tests one endpoint in isolation.
Run with: python manage.py test apps.authentication
"""

from rest_framework import status
from rest_framework.test import APITestCase

from apps.authentication.models import CustomUser
from apps.organizations.models import Organization, OrganizationMembership


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

REGISTER_URL = "/api/auth/register/"
LOGIN_URL    = "/api/auth/login/"
REFRESH_URL  = "/api/auth/refresh/"
LOGOUT_URL   = "/api/auth/logout/"
ME_URL       = "/api/auth/me/"

DEV_PAYLOAD = {
    "email":     "dev@test.id",
    "full_name": "Developer Test",
    "phone":     "+62 812 0000 0001",
    "password":  "DevelopIndo2026!",
    "password2": "DevelopIndo2026!",
    "role":      "developer",
}

BUYER_PAYLOAD = {
    "email":     "buyer@test.id",
    "full_name": "Buyer Test",
    "phone":     "+62 812 0000 0002",
    "password":  "DevelopIndo2026!",
    "password2": "DevelopIndo2026!",
    "role":      "buyer",
}


def _register(client, payload=None):
    """Register and return the full response data."""
    return client.post(REGISTER_URL, payload or DEV_PAYLOAD, format="json")


def _login(client, email="dev@test.id", password="DevelopIndo2026!"):
    return client.post(LOGIN_URL, {"email": email, "password": password}, format="json")


def _auth_header(token):
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


# =============================================================================
# 1. Registration
# =============================================================================

class RegisterViewTests(APITestCase):
    """POST /api/auth/register/"""

    # ── Happy paths ───────────────────────────────────────────

    def test_developer_registration_returns_201_with_tokens(self):
        resp = _register(self.client)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data["success"])
        self.assertIn("access",  resp.data)
        self.assertIn("refresh", resp.data)
        self.assertIn("user",    resp.data)

    def test_developer_registration_creates_user_with_correct_role(self):
        _register(self.client)
        user = CustomUser.objects.get(email="dev@test.id")
        self.assertEqual(user.role, "developer")
        self.assertTrue(user.is_active)

    def test_developer_registration_auto_creates_organization(self):
        """Sprint 0 regression guard — org must exist immediately after register."""
        _register(self.client)
        user = CustomUser.objects.get(email="dev@test.id")
        self.assertTrue(
            OrganizationMembership.objects.filter(user=user, role="owner").exists(),
            "Developer registration must auto-create an owner membership",
        )

    def test_developer_registration_org_name_derived_from_full_name(self):
        _register(self.client)
        user = CustomUser.objects.get(email="dev@test.id")
        membership = OrganizationMembership.objects.get(user=user)
        self.assertIn("Developer Test", membership.organization.name)

    def test_buyer_registration_returns_201(self):
        resp = _register(self.client, BUYER_PAYLOAD)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["user"]["role"], "buyer")

    def test_buyer_registration_does_not_create_organization(self):
        """Buyers belong to a tenant via unit assignment, not org membership."""
        _register(self.client, BUYER_PAYLOAD)
        user = CustomUser.objects.get(email="buyer@test.id")
        self.assertFalse(
            OrganizationMembership.objects.filter(user=user).exists(),
            "Buyer registration must NOT create an Organization",
        )

    def test_response_user_object_contains_expected_fields(self):
        resp = _register(self.client)
        user = resp.data["user"]
        for field in ("id", "email", "full_name", "role", "role_display", "is_active"):
            self.assertIn(field, user, f"Missing field: {field}")

    # ── Validation failures ───────────────────────────────────

    def test_mismatched_passwords_returns_400(self):
        payload = {**DEV_PAYLOAD, "password2": "WrongPassword!"}
        resp = _register(self.client, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data["success"])

    def test_duplicate_email_returns_400(self):
        _register(self.client)
        resp = _register(self.client)  # same email again
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_returns_400(self):
        payload = {**DEV_PAYLOAD}
        del payload["email"]
        resp = _register(self.client, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        payload = {**DEV_PAYLOAD}
        del payload["password"]
        resp = _register(self.client, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_role_returns_400(self):
        """Only developer and buyer are self-registerable."""
        payload = {**DEV_PAYLOAD, "email": "admin@test.id", "role": "super_admin"}
        resp = _register(self.client, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_returns_400(self):
        payload = {**DEV_PAYLOAD, "password": "123", "password2": "123"}
        resp = _register(self.client, payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# 2. Login
# =============================================================================

class LoginViewTests(APITestCase):
    """POST /api/auth/login/"""

    def setUp(self):
        _register(self.client)  # creates dev@test.id

    # ── Happy paths ───────────────────────────────────────────

    def test_valid_credentials_return_200_with_tokens(self):
        resp = _login(self.client)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertIn("access",  resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_response_contains_user_object(self):
        resp = _login(self.client)
        self.assertIn("user", resp.data)
        self.assertEqual(resp.data["user"]["email"], "dev@test.id")

    def test_login_returns_correct_role(self):
        resp = _login(self.client)
        self.assertEqual(resp.data["user"]["role"], "developer")

    def test_access_token_is_usable_on_protected_endpoint(self):
        """The returned access token must actually work."""
        token = _login(self.client).data["access"]
        resp = self.client.get(ME_URL, **_auth_header(token))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # ── Failure cases ─────────────────────────────────────────

    def test_wrong_password_returns_400(self):
        resp = _login(self.client, password="WrongPassword!")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(resp.data["success"])

    def test_nonexistent_email_returns_400(self):
        resp = _login(self.client, email="nobody@test.id")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_returns_400(self):
        resp = self.client.post(LOGIN_URL, {"password": "DevelopIndo2026!"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        resp = self.client.post(LOGIN_URL, {"email": "dev@test.id"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_body_returns_400(self):
        resp = self.client.post(LOGIN_URL, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_user_cannot_login(self):
        """Deactivated accounts must be rejected."""
        user = CustomUser.objects.get(email="dev@test.id")
        user.is_active = False
        user.save()
        resp = _login(self.client)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# 3. Token Refresh
# =============================================================================

class RefreshViewTests(APITestCase):
    """POST /api/auth/refresh/"""

    def setUp(self):
        _register(self.client)
        resp = _login(self.client)
        self.refresh_token = resp.data["refresh"]
        self.access_token  = resp.data["access"]

    # ── Happy paths ───────────────────────────────────────────

    def test_valid_refresh_token_returns_new_access_token(self):
        resp = self.client.post(REFRESH_URL, {"refresh": self.refresh_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertIn("access", resp.data)

    def test_new_access_token_is_usable(self):
        """The refreshed token must actually authenticate."""
        new_access = self.client.post(
            REFRESH_URL, {"refresh": self.refresh_token}, format="json"
        ).data["access"]
        resp = self.client.get(ME_URL, **_auth_header(new_access))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_new_access_token_is_different_from_original(self):
        """Refresh should issue a brand-new token, not echo the old one."""
        new_access = self.client.post(
            REFRESH_URL, {"refresh": self.refresh_token}, format="json"
        ).data["access"]
        self.assertNotEqual(new_access, self.access_token)

    # ── Failure cases ─────────────────────────────────────────

    def test_invalid_refresh_token_returns_401(self):
        resp = self.client.post(REFRESH_URL, {"refresh": "not.a.real.token"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(resp.data["success"])

    def test_missing_refresh_token_returns_400(self):
        resp = self.client.post(REFRESH_URL, {}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_blacklisted_refresh_token_returns_401(self):
        """After logout, the refresh token must be dead."""
        # Logout to blacklist the token
        token = _login(self.client).data["access"]
        self.client.post(
            LOGOUT_URL,
            {"refresh": self.refresh_token},
            format="json",
            **_auth_header(token),
        )
        # Now try to refresh with the blacklisted token
        resp = self.client.post(REFRESH_URL, {"refresh": self.refresh_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# 4. Logout
# =============================================================================

class LogoutViewTests(APITestCase):
    """POST /api/auth/logout/"""

    def setUp(self):
        _register(self.client)
        resp = _login(self.client)
        self.access_token  = resp.data["access"]
        self.refresh_token = resp.data["refresh"]

    def _logout(self, access=None, refresh=None):
        return self.client.post(
            LOGOUT_URL,
            {"refresh": refresh or self.refresh_token},
            format="json",
            **_auth_header(access or self.access_token),
        )

    # ── Happy paths ───────────────────────────────────────────

    def test_logout_returns_200(self):
        resp = self._logout()
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])

    def test_refresh_token_is_blacklisted_after_logout(self):
        """Core security guarantee — the refresh token must be dead after logout."""
        self._logout()
        resp = self.client.post(REFRESH_URL, {"refresh": self.refresh_token}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_logout_twice_with_same_token(self):
        """A blacklisted token cannot be blacklisted again."""
        self._logout()
        resp = self._logout()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    # ── Auth enforcement ─────────────────────────────────────

    def test_logout_requires_authentication(self):
        """Unauthenticated logout must be rejected — not silently accepted."""
        resp = self.client.post(
            LOGOUT_URL, {"refresh": self.refresh_token}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_missing_refresh_token_returns_400(self):
        resp = self.client.post(
            LOGOUT_URL, {}, format="json", **_auth_header(self.access_token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_with_invalid_refresh_token_returns_400(self):
        resp = self.client.post(
            LOGOUT_URL,
            {"refresh": "not.a.valid.token"},
            format="json",
            **_auth_header(self.access_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# 5. Me (profile)
# =============================================================================

class MeViewTests(APITestCase):
    """GET + PUT /api/auth/me/"""

    def setUp(self):
        _register(self.client)
        self.access_token = _login(self.client).data["access"]

    # ── GET ───────────────────────────────────────────────────

    def test_get_me_returns_200_with_user(self):
        resp = self.client.get(ME_URL, **_auth_header(self.access_token))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data["success"])
        self.assertEqual(resp.data["user"]["email"], "dev@test.id")

    def test_get_me_returns_correct_fields(self):
        resp = self.client.get(ME_URL, **_auth_header(self.access_token))
        user = resp.data["user"]
        for field in ("id", "email", "full_name", "phone", "role", "is_active"):
            self.assertIn(field, user, f"Missing field in /me/ response: {field}")

    def test_get_me_without_token_returns_401(self):
        resp = self.client.get(ME_URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_me_with_invalid_token_returns_401(self):
        resp = self.client.get(ME_URL, **_auth_header("invalid.token.here"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── PUT ───────────────────────────────────────────────────

    def test_put_me_updates_full_name(self):
        resp = self.client.put(
            ME_URL,
            {"full_name": "Updated Name"},
            format="json",
            **_auth_header(self.access_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["user"]["full_name"], "Updated Name")

    def test_put_me_updates_phone(self):
        resp = self.client.put(
            ME_URL,
            {"phone": "+62 812 9999 8888"},
            format="json",
            **_auth_header(self.access_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["user"]["phone"], "+62 812 9999 8888")

    def test_put_me_is_partial_update(self):
        """PUT should not wipe fields that aren't included in the payload."""
        self.client.put(
            ME_URL,
            {"full_name": "Partial Update"},
            format="json",
            **_auth_header(self.access_token),
        )
        user = CustomUser.objects.get(email="dev@test.id")
        # email must be unchanged
        self.assertEqual(user.email, "dev@test.id")

    def test_put_me_cannot_change_role(self):
        """Users must not be able to self-elevate their role."""
        self.client.put(
            ME_URL,
            {"role": "super_admin"},
            format="json",
            **_auth_header(self.access_token),
        )
        user = CustomUser.objects.get(email="dev@test.id")
        self.assertEqual(user.role, "developer")

    def test_put_me_without_token_returns_401(self):
        resp = self.client.put(ME_URL, {"full_name": "Hacker"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# 6. Full auth lifecycle (integration)
# =============================================================================

class AuthLifecycleTests(APITestCase):
    """
    End-to-end: register → login → use token → refresh → logout → dead.
    This is the sequence every real user goes through.
    """

    def test_full_developer_lifecycle(self):
        # 1. Register
        reg = _register(self.client)
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED)
        access  = reg.data["access"]
        refresh = reg.data["refresh"]

        # 2. Verify org created immediately
        user = CustomUser.objects.get(email="dev@test.id")
        self.assertTrue(OrganizationMembership.objects.filter(user=user).exists())

        # 3. Access protected endpoint
        me = self.client.get(ME_URL, **_auth_header(access))
        self.assertEqual(me.status_code, status.HTTP_200_OK)

        # 4. Refresh
        new_access = self.client.post(
            REFRESH_URL, {"refresh": refresh}, format="json"
        ).data["access"]
        self.assertNotEqual(new_access, access)

        # 5. New token works
        me2 = self.client.get(ME_URL, **_auth_header(new_access))
        self.assertEqual(me2.status_code, status.HTTP_200_OK)

        # 6. Logout
        logout = self.client.post(
            LOGOUT_URL, {"refresh": refresh},
            format="json", **_auth_header(new_access),
        )
        self.assertEqual(logout.status_code, status.HTTP_200_OK)

        # 7. Refresh token is now dead
        dead = self.client.post(REFRESH_URL, {"refresh": refresh}, format="json")
        self.assertEqual(dead.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_buyer_lifecycle_no_org_created(self):
        # Register as buyer
        reg = _register(self.client, BUYER_PAYLOAD)
        self.assertEqual(reg.status_code, status.HTTP_201_CREATED)

        # Login works
        login = _login(self.client, email="buyer@test.id")
        self.assertEqual(login.status_code, status.HTTP_200_OK)

        # No org
        user = CustomUser.objects.get(email="buyer@test.id")
        self.assertFalse(OrganizationMembership.objects.filter(user=user).exists())

        # Can access /me/
        me = self.client.get(ME_URL, **_auth_header(login.data["access"]))
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["user"]["role"], "buyer")
