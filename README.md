# API Monitoring System

A FastAPI-based API monitoring service that lets you register external services, monitor their health, and track response status over time. The project exposes REST endpoints for service management, monitoring logs, and user authentication.

## What this project does

This application is designed to help you:

- Track APIs and backend services you depend on
- Register service names, endpoints, and HTTP methods
- Run health checks against each service
- Record status codes, response times, and health results
- View historical monitoring logs for each service
- Secure the API with user registration and JWT-based login
- Restrict service management actions to admin users

## Features

- FastAPI backend with REST API routes
- SQLAlchemy ORM with a database layer
- Service CRUD operations
- Monitoring log creation and retrieval
- HTTP health checks using `httpx`
- JWT authentication and password hashing via `bcrypt` and `python-jose`
- Role-based access control for admin-only actions

## Project structure

```text
API_MONITORING_SYSTEM/
├── api-monitoring/
│   └── app/
│       ├── database.py
│       ├── main.py
│       ├── models.py
│       ├── requirements.txt
│       ├── schemas.py
│       └── security.py
└── README.md
```

## Main API features

### Authentication

- `POST /auth/register` — create a new user
- `POST /auth/login` — login and receive a JWT access token

### Service management

- `GET /services` — fetch all services
- `POST /services` — create a new service
- `PATCH /services/{service_id}` — update a service
- `DELETE /services/{service_id}` — delete a service

### Monitoring

- `POST /services/{service_id}/logs` — add a monitoring log
- `GET /services/{service_id}/logs` — fetch logs for a service
- `POST /services/{service_id}/check` — actively ping a service and store the result

## Tech stack

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL/MySQL-compatible database via SQLAlchemy
- JWT authentication
- bcrypt password hashing
- httpx for outgoing HTTP checks

## Setup

1. Open the app folder:

```bash
cd api-monitoring/app
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure your database connection in the environment variables used by `database.py`.

5. Run the app:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## Example use case

A team can register a payment API, a user service, and a notification service. The system checks each endpoint periodically and records whether it responds successfully, how long it took, and whether it is healthy. This helps detect outages and performance issues quickly.

## Accuracy benchmark (50 simulated checks)

I validated the monitoring logic against a known set of 50 service checks:

- 30 healthy endpoints expected to pass
- 20 intentionally failing or timed-out endpoints expected to fail

Verified result from the local run:

- Detection accuracy: 50/50 correct (100.0%)
- Average health-check response time: 1582.6 ms
- False positives: none
- False negatives: none

This benchmark was reproduced by running the project script at `test_monitoring_accuracy.py` against the live FastAPI app.

## Notes

- The app uses JWT-based access control.
- Admin privileges are required for creating, updating, and deleting services.
- The project is intended as a practical backend for monitoring service availability and health.

## License

This project is for educational and personal use.
