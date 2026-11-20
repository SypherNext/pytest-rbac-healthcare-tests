"""Real appointment creation/listing tests against the live backend.

POST /api/appointments only returns {message, appointmentId} -- not the
full record -- so every creation test follows a POST-then-GET pattern to
check the record actually landed with the right data.
"""

import requests

from helpers import auth_headers, build_test_appointment

BASE_URL = "http://localhost:5000"


def test_nurse_can_create_appointment(logged_in_nurse, logged_in_doctor, logged_in_patient):
    doctor_id = logged_in_doctor["user"]["id"]
    patient_id = logged_in_patient["user"]["id"]

    body = build_test_appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date="2026-12-10T09:00:00Z",
        reason="Annual checkup",
    )
    response = requests.post(
        f"{BASE_URL}/api/appointments",
        json=body,
        headers=auth_headers(logged_in_nurse),
    )

    assert response.status_code == 201
    created = response.json()
    assert "appointmentId" in created
    assert isinstance(created["appointmentId"], int)

    # The create response doesn't include the full record -- fetch it.
    fetched = requests.get(
        f"{BASE_URL}/api/appointments/{created['appointmentId']}",
        headers=auth_headers(logged_in_nurse),
    )
    assert fetched.status_code == 200
    record = fetched.json()
    assert record["patient_id"] == patient_id
    assert record["doctor_id"] == doctor_id
    assert record["reason"] == "Annual checkup"
    assert "patient_name" in record
    assert "doctor_name" in record


def test_created_appointment_appears_in_full_list(logged_in_nurse, logged_in_doctor, logged_in_patient):
    doctor_id = logged_in_doctor["user"]["id"]
    patient_id = logged_in_patient["user"]["id"]

    body = build_test_appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date="2026-12-11T09:00:00Z",
        reason="Follow-up visit",
        notes="Bring prior lab results",
    )
    created = requests.post(
        f"{BASE_URL}/api/appointments",
        json=body,
        headers=auth_headers(logged_in_nurse),
    ).json()

    # Nurses see the unfiltered list (same as admin -- see test_permissions.py).
    listing = requests.get(
        f"{BASE_URL}/api/appointments",
        headers=auth_headers(logged_in_nurse),
    )
    assert listing.status_code == 200
    ids_in_list = [appt["id"] for appt in listing.json()]
    assert created["appointmentId"] in ids_in_list


def test_patient_appointment_list_is_filtered_to_own(logged_in_patient, logged_in_doctor):
    doctor_id = logged_in_doctor["user"]["id"]
    patient_id = logged_in_patient["user"]["id"]

    # Patients are allowed to create their own appointment too -- the API
    # does not restrict POST /api/appointments by role (see test_permissions.py).
    body = build_test_appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date="2026-12-12T09:00:00Z",
        reason="Self-booked visit",
    )
    requests.post(
        f"{BASE_URL}/api/appointments",
        json=body,
        headers=auth_headers(logged_in_patient),
    )

    listing = requests.get(
        f"{BASE_URL}/api/appointments",
        headers=auth_headers(logged_in_patient),
    )
    assert listing.status_code == 200
    appointments = listing.json()
    assert len(appointments) > 0
    assert all(appt["patient_id"] == patient_id for appt in appointments)


def test_get_single_appointment_not_found_returns_404(logged_in_admin):
    response = requests.get(
        f"{BASE_URL}/api/appointments/999999",
        headers=auth_headers(logged_in_admin),
    )
    assert response.status_code == 404
