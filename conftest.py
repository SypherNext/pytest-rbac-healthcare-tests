"""Shared fixtures for the whole project.

Anything defined here is automatically available to every test_*.py file
in this folder -- no import needed. See helpers.py for plain functions,
which still need an explicit import.
"""

import pytest
import requests

BASE_URL = "http://localhost:5000"

# Seeded accounts in rbac-healthcare-system. The default admin keeps its
# own password; every other seeded user shares "pass@123".
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}
DOCTOR_CREDENTIALS = {"username": "doctor1", "password": "pass@123"}
NURSE_CREDENTIALS = {"username": "nurse1", "password": "pass@123"}
PATIENT_CREDENTIALS = {"username": "patient1", "password": "pass@123"}


def _login(credentials):
    response = requests.post(f"{BASE_URL}/api/auth/login", json=credentials)
    return response.json()


@pytest.fixture
def logged_in_admin():
    return _login(ADMIN_CREDENTIALS)


@pytest.fixture
def logged_in_doctor():
    return _login(DOCTOR_CREDENTIALS)


@pytest.fixture
def logged_in_nurse():
    return _login(NURSE_CREDENTIALS)


@pytest.fixture
def logged_in_patient():
    return _login(PATIENT_CREDENTIALS)
