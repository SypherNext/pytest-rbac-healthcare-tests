# pytest-rbac-healthcare-tests

A real pytest test suite for the **rbac-healthcare-system** backend — the
reference implementation for the "Structuring a Simple Test Project" and
"Capstone" lessons in the *Python for Test Automation* course.

This is not a toy: every test here makes a real HTTP request to a running
instance of `rbac-healthcare-system`'s backend and asserts on its actual
response, including a few places where the live API's enforcement
differs from the permission table in that app's own README (see the
comments in `test_permissions.py`).

## Project layout

```text
pytest-rbac-healthcare-tests/
├── requirements.txt
├── pytest.ini
├── conftest.py
├── helpers.py
├── test_login.py
├── test_appointments.py
└── test_permissions.py
```

- `conftest.py` — shared login fixtures (`logged_in_admin`, `logged_in_doctor`,
  `logged_in_nurse`, `logged_in_patient`). Available to every test file with
  no import, because pytest auto-discovers `conftest.py`.
- `helpers.py` — plain functions (`build_test_appointment`,
  `build_test_medical_record`, `auth_headers`) imported explicitly where
  they're used.
- `test_login.py`, `test_appointments.py`, `test_permissions.py` — the actual
  tests.

## Prerequisites

1. **Python 3.9+** on your machine.
2. A running copy of **rbac-healthcare-system**'s backend, reachable at
   `http://localhost:5000`. This suite does not start the backend for you —
   clone and run it separately, then leave it running:

   ```bash
   git clone https://github.com/codedbyabhishekc/rbac-healthcare-system
   cd rbac-healthcare-system/backend
   npm install
   npm start
   ```

   Confirm it's up before running this suite:

   ```bash
   curl http://localhost:5000/health
   ```

   Swagger UI (useful if you want to see every endpoint and schema) is at
   `http://localhost:5000/api-docs`.

3. The backend's seeded accounts (created by its own setup/seed step):
   - `admin` / `admin123`
   - every other seeded user (`admin1`-`admin3`, `doctor1`-`doctor8`,
     `nurse1`-`nurse7`, `patient1`-`patient15`) / `pass@123`

   This suite logs in as `admin`, `doctor1`, `nurse1`, and `patient1` by
   default (see `conftest.py`) — if your backend's seed data differs,
   update the credentials there.

## Setup

### Windows (PowerShell)

```powershell
git clone <this-repo-url> pytest-rbac-healthcare-tests
cd pytest-rbac-healthcare-tests
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
git clone <this-repo-url> pytest-rbac-healthcare-tests
cd pytest-rbac-healthcare-tests
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the tests

With the backend running at `http://localhost:5000` and your virtual
environment activated:

```bash
pytest
```

For more detail per test:

```bash
pytest -v
```

To run just one file:

```bash
pytest test_permissions.py -v
```

## What's being tested

- `test_login.py` — real logins for each role, checking the token and
  user-object shape the API actually returns.
- `test_appointments.py` — creating appointments with the real snake_case
  schema (`patient_id`, `doctor_id`, `appointment_date`, `reason`), then
  following up with a `GET` since the create endpoint only returns
  `{message, appointmentId}`, not the full record.
- `test_permissions.py` — a live version of the capstone's permission-matrix
  exercise. Instead of checking a local `has_permission()` stand-in, it logs
  in as each role and calls the real API, asserting on the actual
  enforcement it gets back — including a couple of places where that
  enforcement is looser than the app's own documented permission table
  (explained in comments right above those tests).

## Notes

- Tests that create data (appointments, medical records) create their own
  throwaway rows and don't assume a particular starting database state,
  except where noted (medical-record and appointment list-filtering tests
  assume at least one pre-seeded record exists for the doctor/patient used).
- Re-running the suite repeatedly will add more rows to the backend's local
  database — that's expected for a suite exercising a real API.

## License

Copyright (C) 2026 SypherNext

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0). You may
use, study and change it. If you share a modified version, or run one as a website or service
that other people use, you must make your full modified source code available under the same
license. See [LICENSE](LICENSE) for the full terms.
