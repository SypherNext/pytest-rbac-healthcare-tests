"""Plain helper functions shared across test files.

Unlike the fixtures in conftest.py, anything in here needs an explicit
`from helpers import ...` in whichever test file uses it.
"""

BASE_URL = "http://localhost:5000"


def auth_headers(logged_in_user):
    """Build an Authorization header dict from a logged-in fixture's JSON."""
    return {"Authorization": f"Bearer {logged_in_user['token']}"}


def build_test_appointment(patient_id, doctor_id, appointment_date, reason, notes=None):
    """Build a request body for POST /api/appointments.

    Matches the real API schema: snake_case fields, numeric ids.
    """
    body = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "reason": reason,
    }
    if notes is not None:
        body["notes"] = notes
    return body


def build_test_medical_record(patient_id, diagnosis, prescription=None, notes=None):
    """Build a request body for POST /api/medical-records."""
    body = {
        "patient_id": patient_id,
        "diagnosis": diagnosis,
    }
    if prescription is not None:
        body["prescription"] = prescription
    if notes is not None:
        body["notes"] = notes
    return body
