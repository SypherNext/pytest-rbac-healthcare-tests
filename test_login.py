"""Real login tests against the live rbac-healthcare-system backend.

Each test logs in as a different seeded role and checks the shape of the
response: a JWT `token` string plus a `user` object with the fields the
API actually returns (id, username, email, role, full_name).
"""

import requests

BASE_URL = "http://localhost:5000"


def test_admin_login_returns_token(logged_in_admin):
    assert "token" in logged_in_admin
    assert isinstance(logged_in_admin["token"], str)
    assert len(logged_in_admin["token"]) > 0


def test_admin_login_returns_expected_user_fields(logged_in_admin):
    user = logged_in_admin["user"]
    assert user["username"] == "admin"
    assert user["role"] == "Administrator"
    assert "id" in user
    assert "email" in user
    assert "full_name" in user


def test_doctor_login_returns_token(logged_in_doctor):
    assert "token" in logged_in_doctor
    assert logged_in_doctor["user"]["role"] == "Doctor"


def test_nurse_login_returns_token(logged_in_nurse):
    assert "token" in logged_in_nurse
    assert logged_in_nurse["user"]["role"] == "Nurse"


def test_patient_login_returns_token(logged_in_patient):
    assert "token" in logged_in_patient
    assert logged_in_patient["user"]["role"] == "Patient"


def test_wrong_password_is_rejected():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "not-the-right-password"},
    )
    assert response.status_code in (401, 400)
    assert "token" not in response.json()


def test_unknown_username_is_rejected():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "no-such-user", "password": "pass@123"},
    )
    assert response.status_code in (401, 404, 400)
