"""Real pytest version of the capstone's permission-matrix exercise.

The capstone builds `has_permission(role, action)` against a local dict
standing in for the rules in rbac-healthcare-system's own README. Here we
point the same idea at the live API instead: log in as each role, make
the real request, and assert on what the backend actually does.

A couple of these tests deliberately capture *real, verified* behavior
that differs from the README's permission table -- the table describes
the intended policy, but the API code (src/routes/*.routes.js) doesn't
enforce every row of it. Each divergence is called out in a comment,
confirmed by actually running the request against localhost:5000 while
writing this file -- not assumed from the table.
"""

import pytest
import requests

from helpers import auth_headers, build_test_appointment, build_test_medical_record

BASE_URL = "http://localhost:5000"


def _fixture_for(request, role):
    """Look up the right logged_in_<role> fixture by name."""
    return request.getfixturevalue(f"logged_in_{role}")


# ---------------------------------------------------------------------------
# "View all users" -- matches the README matrix exactly: Admin only.
# ---------------------------------------------------------------------------

PERMISSION_CASES_VIEW_ALL_USERS = [
    ("admin", True),
    ("doctor", False),
    ("nurse", False),
    ("patient", False),
]


@pytest.mark.parametrize("role,expected_allowed", PERMISSION_CASES_VIEW_ALL_USERS)
def test_view_all_users_matches_matrix(request, role, expected_allowed):
    logged_in_user = _fixture_for(request, role)
    response = requests.get(f"{BASE_URL}/api/users", headers=auth_headers(logged_in_user))

    if expected_allowed:
        assert response.status_code == 200
    else:
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# "Create medical records" -- matches the README matrix exactly: Doctor only.
# ---------------------------------------------------------------------------

PERMISSION_CASES_CREATE_MEDICAL_RECORD = [
    ("admin", False),
    ("doctor", True),
    ("nurse", False),
    ("patient", False),
]


@pytest.mark.parametrize("role,expected_allowed", PERMISSION_CASES_CREATE_MEDICAL_RECORD)
def test_create_medical_record_matches_matrix(request, role, expected_allowed, logged_in_patient):
    logged_in_user = _fixture_for(request, role)
    body = build_test_medical_record(
        patient_id=logged_in_patient["user"]["id"],
        diagnosis="RBAC permission-matrix check",
    )
    response = requests.post(
        f"{BASE_URL}/api/medical-records", json=body, headers=auth_headers(logged_in_user)
    )

    if expected_allowed:
        assert response.status_code == 201
    else:
        assert response.status_code == 403


# ---------------------------------------------------------------------------
# "Cancel/complete appointments" -- PUT /api/appointments/:id.
# Real behavior: Administrator, Doctor and Nurse can all update status
# (the route doesn't distinguish "complete" from "cancel" -- it's one
# generic update endpoint gated by role, not by which status is being
# set). This is coarser than the matrix's separate Complete/Cancel rows,
# but it IS consistent with "Patient: No" for both.
# ---------------------------------------------------------------------------

PERMISSION_CASES_UPDATE_APPOINTMENT = [
    ("admin", True),
    ("doctor", True),
    ("nurse", True),
    ("patient", False),
]


@pytest.mark.parametrize("role,expected_allowed", PERMISSION_CASES_UPDATE_APPOINTMENT)
def test_update_appointment_status_matches_real_enforcement(
    request, role, expected_allowed, logged_in_nurse, logged_in_doctor, logged_in_patient
):
    # Create a fresh throwaway appointment for each case so tests don't
    # fight over shared state.
    created = requests.post(
        f"{BASE_URL}/api/appointments",
        json=build_test_appointment(
            patient_id=logged_in_patient["user"]["id"],
            doctor_id=logged_in_doctor["user"]["id"],
            appointment_date="2026-12-15T09:00:00Z",
            reason="permission matrix check",
        ),
        headers=auth_headers(logged_in_nurse),
    ).json()

    logged_in_user = _fixture_for(request, role)
    response = requests.put(
        f"{BASE_URL}/api/appointments/{created['appointmentId']}",
        json={"status": "completed"},
        headers=auth_headers(logged_in_user),
    )

    if expected_allowed:
        assert response.status_code == 200
    else:
        assert response.status_code == 403

    # Clean up with admin regardless of who succeeded above.
    requests.delete(
        f"{BASE_URL}/api/appointments/{created['appointmentId']}",
        headers=auth_headers(request.getfixturevalue("logged_in_admin")),
    )


# ---------------------------------------------------------------------------
# "View medical records" -- DIVERGES from the matrix.
# The matrix says Nurse: No. The real route (medicalRecord.routes.js) only
# adds a WHERE filter for Patient and Doctor; Nurse falls through
# unfiltered, same as Administrator. Verified live: a nurse's record
# count equals the admin's unfiltered count, not zero/403.
# ---------------------------------------------------------------------------


def test_nurse_can_in_fact_view_all_medical_records(logged_in_nurse, logged_in_admin):
    """Documents a real divergence from the README matrix, not a bug we're
    fixing here -- the matrix says Nurse should be denied, but the API
    currently lets nurses see every medical record, same as an admin."""
    admin_response = requests.get(
        f"{BASE_URL}/api/medical-records", headers=auth_headers(logged_in_admin)
    )
    nurse_response = requests.get(
        f"{BASE_URL}/api/medical-records", headers=auth_headers(logged_in_nurse)
    )

    assert admin_response.status_code == 200
    assert nurse_response.status_code == 200
    assert len(nurse_response.json()) == len(admin_response.json())


def test_doctor_medical_record_view_is_filtered_to_own_patients(logged_in_doctor):
    response = requests.get(f"{BASE_URL}/api/medical-records", headers=auth_headers(logged_in_doctor))
    assert response.status_code == 200
    records = response.json()
    assert len(records) > 0
    assert all(record["doctor_id"] == logged_in_doctor["user"]["id"] for record in records)


def test_patient_medical_record_view_is_filtered_to_own_records(logged_in_patient):
    response = requests.get(f"{BASE_URL}/api/medical-records", headers=auth_headers(logged_in_patient))
    assert response.status_code == 200
    records = response.json()
    assert len(records) > 0
    assert all(record["patient_id"] == logged_in_patient["user"]["id"] for record in records)


# ---------------------------------------------------------------------------
# "Schedule appointments" -- DIVERGES from the matrix.
# The matrix says only Nurse: Yes. The real route (POST /api/appointments)
# has no role check at all, so every role can create an appointment.
# ---------------------------------------------------------------------------


def test_every_role_can_in_fact_create_appointments(
    logged_in_admin, logged_in_doctor, logged_in_nurse, logged_in_patient
):
    """Documents a real divergence from the README matrix: the matrix
    restricts scheduling to Nurse, but POST /api/appointments has no
    authorizeRoles() middleware, so every role succeeds."""
    doctor_id = logged_in_doctor["user"]["id"]
    patient_id = logged_in_patient["user"]["id"]

    for role_label, actor in [
        ("admin", logged_in_admin),
        ("doctor", logged_in_doctor),
        ("nurse", logged_in_nurse),
        ("patient", logged_in_patient),
    ]:
        body = build_test_appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date="2026-12-16T09:00:00Z",
            reason=f"schedule-matrix-check-{role_label}",
        )
        response = requests.post(
            f"{BASE_URL}/api/appointments", json=body, headers=auth_headers(actor)
        )
        assert response.status_code == 201, f"{role_label} should be able to create an appointment"

        # Clean up immediately so these throwaway rows don't pile up.
        requests.delete(
            f"{BASE_URL}/api/appointments/{response.json()['appointmentId']}",
            headers=auth_headers(logged_in_admin),
        )


# ---------------------------------------------------------------------------
# "View all appointments" -- matches the matrix: Admin and Nurse see every
# appointment unfiltered; Doctor and Patient are filtered to their own.
# ---------------------------------------------------------------------------


def test_admin_and_nurse_see_unfiltered_appointment_list(logged_in_admin, logged_in_nurse):
    admin_response = requests.get(f"{BASE_URL}/api/appointments", headers=auth_headers(logged_in_admin))
    nurse_response = requests.get(f"{BASE_URL}/api/appointments", headers=auth_headers(logged_in_nurse))

    assert admin_response.status_code == 200
    assert nurse_response.status_code == 200
    assert len(nurse_response.json()) == len(admin_response.json())


def test_doctor_appointment_list_is_filtered_to_own(logged_in_doctor):
    response = requests.get(f"{BASE_URL}/api/appointments", headers=auth_headers(logged_in_doctor))
    assert response.status_code == 200
    appointments = response.json()
    assert all(appt["doctor_id"] == logged_in_doctor["user"]["id"] for appt in appointments)


def test_patient_appointment_list_is_filtered_to_own(logged_in_patient):
    response = requests.get(f"{BASE_URL}/api/appointments", headers=auth_headers(logged_in_patient))
    assert response.status_code == 200
    appointments = response.json()
    assert all(appt["patient_id"] == logged_in_patient["user"]["id"] for appt in appointments)
