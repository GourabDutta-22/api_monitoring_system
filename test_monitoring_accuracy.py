#!/usr/bin/env python3
import os
import sqlite3
import time
from pathlib import Path

import bcrypt
import httpx

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "api-monitoring" / "app"
DB_PATH = APP_DIR / "monitoring.db"
BASE_URL = "http://127.0.0.1:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

SERVICE_CASES = [
    # --- Healthy (expected True) ---
    {"name": "httpbin-200-ok-1", "url": "https://httpbin.org/status/200", "expected": True},
    {"name": "httpbin-200-ok-2", "url": "https://httpbin.org/status/201", "expected": True},
    {"name": "httpbin-200-ok-3", "url": "https://httpbin.org/status/204", "expected": True},
    {"name": "httpbin-get-200", "url": "https://httpbin.org/get", "expected": True},
    {"name": "httpbin-uuid-200", "url": "https://httpbin.org/uuid", "expected": True},
    {"name": "httpbin-anything-200", "url": "https://httpbin.org/anything", "expected": True},
    {"name": "httpbin-ip-200", "url": "https://httpbin.org/ip", "expected": True},
    {"name": "httpbin-user-agent-200", "url": "https://httpbin.org/user-agent", "expected": True},
    {"name": "httpbin-headers-200", "url": "https://httpbin.org/headers", "expected": True},
    {"name": "httpbin-json-200", "url": "https://httpbin.org/json", "expected": True},
    {"name": "httpbin-html-200", "url": "https://httpbin.org/html", "expected": True},
    {"name": "httpbin-xml-200", "url": "https://httpbin.org/xml", "expected": True},
    {"name": "httpbin-gzip-200", "url": "https://httpbin.org/gzip", "expected": True},
    {"name": "httpbin-deflate-200", "url": "https://httpbin.org/deflate", "expected": True},
    {"name": "httpbin-cache-200", "url": "https://httpbin.org/cache", "expected": True},
    {"name": "httpbin-robots-200", "url": "https://httpbin.org/robots.txt", "expected": True},
    {"name": "httpbin-base64-200", "url": "https://httpbin.org/base64/aGVsbG8=", "expected": True},
    {"name": "httpbin-links-200", "url": "https://httpbin.org/links/5/0", "expected": True},
    {"name": "jsonplaceholder-todo-1", "url": "https://jsonplaceholder.typicode.com/todos/1", "expected": True},
    {"name": "jsonplaceholder-todo-2", "url": "https://jsonplaceholder.typicode.com/todos/2", "expected": True},
    {"name": "jsonplaceholder-todo-3", "url": "https://jsonplaceholder.typicode.com/todos/3", "expected": True},
    {"name": "jsonplaceholder-post-1", "url": "https://jsonplaceholder.typicode.com/posts/1", "expected": True},
    {"name": "jsonplaceholder-post-2", "url": "https://jsonplaceholder.typicode.com/posts/2", "expected": True},
    {"name": "jsonplaceholder-post-3", "url": "https://jsonplaceholder.typicode.com/posts/3", "expected": True},
    {"name": "jsonplaceholder-user-1", "url": "https://jsonplaceholder.typicode.com/users/1", "expected": True},
    {"name": "jsonplaceholder-user-2", "url": "https://jsonplaceholder.typicode.com/users/2", "expected": True},
    {"name": "jsonplaceholder-user-3", "url": "https://jsonplaceholder.typicode.com/users/3", "expected": True},
    {"name": "jsonplaceholder-comment-1", "url": "https://jsonplaceholder.typicode.com/comments/1", "expected": True},
    {"name": "jsonplaceholder-comment-2", "url": "https://jsonplaceholder.typicode.com/comments/2", "expected": True},
    {"name": "reqres-user-2", "url": "https://reqres.in/api/users/2", "expected": True},

    # --- Broken / unhealthy (expected False) ---
    {"name": "httpbin-400-bad", "url": "https://httpbin.org/status/400", "expected": False},
    {"name": "httpbin-401-bad", "url": "https://httpbin.org/status/401", "expected": False},
    {"name": "httpbin-403-bad", "url": "https://httpbin.org/status/403", "expected": False},
    {"name": "httpbin-404-bad", "url": "https://httpbin.org/status/404", "expected": False},
    {"name": "httpbin-405-bad", "url": "https://httpbin.org/status/405", "expected": False},
    {"name": "httpbin-406-bad", "url": "https://httpbin.org/status/406", "expected": False},
    {"name": "httpbin-410-bad", "url": "https://httpbin.org/status/410", "expected": False},
    {"name": "httpbin-418-bad", "url": "https://httpbin.org/status/418", "expected": False},
    {"name": "httpbin-422-bad", "url": "https://httpbin.org/status/422", "expected": False},
    {"name": "httpbin-429-bad", "url": "https://httpbin.org/status/429", "expected": False},
    {"name": "httpbin-500-bad", "url": "https://httpbin.org/status/500", "expected": False},
    {"name": "httpbin-501-bad", "url": "https://httpbin.org/status/501", "expected": False},
    {"name": "httpbin-502-bad", "url": "https://httpbin.org/status/502", "expected": False},
    {"name": "httpbin-503-bad", "url": "https://httpbin.org/status/503", "expected": False},
    {"name": "httpbin-504-bad", "url": "https://httpbin.org/status/504", "expected": False},
    {"name": "nonexistent-domain-1", "url": "https://nonexistent.invalid.example/health", "expected": False},
    {"name": "nonexistent-domain-2", "url": "https://this-does-not-exist-12345.invalid/health", "expected": False},
    {"name": "nonexistent-domain-3", "url": "https://fake-service-9876.invalid/status", "expected": False},
    {"name": "httpbin-delay-10-timeout", "url": "https://httpbin.org/delay/10", "expected": False},
    {"name": "httpbin-delay-15-timeout", "url": "https://httpbin.org/delay/15", "expected": False},
]


def wait_for_server(timeout_seconds: int = 40) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = httpx.get(f"{BASE_URL}/docs", timeout=5)
            if response.status_code < 500:
                return
        except Exception:
            time.sleep(1)
    raise RuntimeError("FastAPI server did not become ready in time.")


def ensure_admin_user() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (ADMIN_USERNAME,),
        ).fetchone()
        if existing is None:
            password_hash = bcrypt.hashpw(
                ADMIN_PASSWORD.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")
            conn.execute(
                "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (ADMIN_USERNAME, "admin@example.com", password_hash, "admin"),
            )
            conn.commit()
    finally:
        conn.close()


def reset_mock_services() -> None:
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("DELETE FROM monitoring_logs")
        conn.execute("DELETE FROM services")
        conn.commit()
    finally:
        conn.close()


def login_and_get_token() -> str:
    response = httpx.post(
        f"{BASE_URL}/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Login failed: {response.status_code} {response.text}")
    return response.json()["access_token"]


def create_services(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    created = []
    for service in SERVICE_CASES:
        response = httpx.post(
            f"{BASE_URL}/services",
            json={
                "name": service["name"],
                "endpoint": service["url"],
                "method": "GET",
            },
            headers=headers,
            timeout=20,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Could not create service {service['name']}: "
                f"{response.status_code} {response.text}"
            )
        payload = response.json()
        created.append(
            {
                "id": payload["id"],
                "name": payload["name"],
                "endpoint": payload["endpoint"],
                "expected": service["expected"],
            }
        )
    return created


def check_services(token: str, services):
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    total_response_ms = 0.0

    for service in services:
        response = httpx.post(
            f"{BASE_URL}/services/{service['id']}/check",
            headers=headers,
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Health check failed for {service['name']}: "
                f"{response.status_code} {response.text}"
            )

        body = response.json()
        actual = bool(body["is_healthy"])
        expected = bool(service["expected"])
        response_time = int(body.get("response_time", 0))
        total_response_ms += response_time

        results.append(
            {
                "service": service["name"],
                "endpoint": service["endpoint"],
                "expected": expected,
                "actual": actual,
                "response_time": response_time,
                "correct": actual == expected,
            }
        )

    average_response_ms = total_response_ms / len(results) if results else 0.0
    return results, average_response_ms


def print_results_table(results):
    print("\nHealth-check accuracy results")
    print("-" * 140)
    print(
        f"{'#':<2} {'Service':<28} {'Expected':<10} {'Actual':<10} {'Response (ms)':>14} {'Correct':<8}"
    )
    print("-" * 140)

    for idx, row in enumerate(results, start=1):
        print(
            f"{idx:<2} {row['service']:<28} "
            f"{str(row['expected']).lower():<10} "
            f"{str(row['actual']).lower():<10} "
            f"{row['response_time']:>14} "
            f"{str(row['correct']).lower():<8}"
        )

    print("-" * 140)


def main():
    print("Waiting for API to become ready...")
    wait_for_server()
    ensure_admin_user()
    reset_mock_services()

    token = login_and_get_token()
    services = create_services(token)
    results, average_ms = check_services(token, services)

    correct_count = sum(1 for row in results if row["correct"])
    accuracy_pct = (correct_count / len(results)) * 100 if results else 0.0

    false_positives = [
        row["service"] for row in results if row["actual"] is True and row["expected"] is False
    ]
    false_negatives = [
        row["service"] for row in results if row["actual"] is False and row["expected"] is True
    ]

    print_results_table(results)
    print(f"\nDetection accuracy: {correct_count}/{len(results)} correct ({accuracy_pct:.1f}%)")
    print(f"Average health-check response time: {average_ms:.1f} ms")
    print(f"False positives: {false_positives if false_positives else 'none'}")
    print(f"False negatives: {false_negatives if false_negatives else 'none'}")


if __name__ == "__main__":
    main()
