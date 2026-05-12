from __future__ import annotations

import base64
import csv
import io
import json
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any


USER_SERVICE_URL = "http://user-service:8001"
DOCUMENT_SERVICE_URL = "http://document-service:8002"
PROMETHEUS_URL = "http://prometheus:9090"
GRAFANA_URL = "http://grafana:3000"
HTTP_TIMEOUT_SECONDS = 10
WAIT_TIMEOUT_SECONDS = 60
POLL_INTERVAL_SECONDS = 2


def _basic_auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> tuple[int, bytes, dict[str, str]]:
    req = urllib.request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return response.status, response.read(), dict(response.headers.items())
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(), dict(exc.headers.items())


def request_json(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: Any | None = None,
) -> tuple[int, Any]:
    merged_headers = dict(headers or {})
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        merged_headers["Content-Type"] = "application/json"
    status, raw_body, _ = request(url, method=method, headers=merged_headers, data=body)
    parsed = json.loads(raw_body.decode("utf-8")) if raw_body else None
    return status, parsed


def build_multipart_form(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = f"----runtime-test-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )

    for name, (filename, content, content_type) in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{filename}"\r\n'
                ).encode("utf-8"),
                f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
                content,
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def wait_until(assertion, *, timeout: int = WAIT_TIMEOUT_SECONDS, interval: int = POLL_INTERVAL_SECONDS, message: str = "condition not met") -> Any:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            result = assertion()
            if result:
                return result
        except Exception as exc:  # pragma: no cover - retry helper
            last_error = exc
        time.sleep(interval)
    if last_error:
        raise AssertionError(f"{message}: {last_error}") from last_error
    raise AssertionError(message)


def wait_for_http_ok(url: str) -> None:
    def probe() -> bool:
        status, _, _ = request(url)
        return status == 200

    wait_until(probe, message=f"{url} did not become ready")


def prometheus_query(expr: str) -> float | None:
    query = urllib.parse.urlencode({"query": expr})
    status, payload = request_json(f"{PROMETHEUS_URL}/api/v1/query?{query}")
    if status != 200:
        raise AssertionError(f"Prometheus query failed with status {status}: {payload}")
    result = payload["data"]["result"]
    if not result:
        return None
    return float(result[0]["value"][1])


class StackRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        wait_for_http_ok(f"{USER_SERVICE_URL}/docs")
        wait_for_http_ok(f"{DOCUMENT_SERVICE_URL}/docs")
        wait_for_http_ok(f"{PROMETHEUS_URL}/-/ready")
        wait_for_http_ok(f"{GRAFANA_URL}/api/health")

    def test_grafana_dashboards_are_provisioned(self) -> None:
        auth_header = {"Authorization": _basic_auth_header("admin", "admin")}

        status, health = request_json(f"{GRAFANA_URL}/api/health", headers=auth_header)
        self.assertEqual(status, 200)
        self.assertEqual(health["database"], "ok")

        for uid in ("application-observability", "infrastructure-observability"):
            status, payload = request_json(
                f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
                headers=auth_header,
            )
            self.assertEqual(status, 200)
            self.assertEqual(payload["dashboard"]["uid"], uid)

    def test_user_service_runtime_and_metrics(self) -> None:
        email = f"ada-{uuid.uuid4().hex[:8]}@example.com"
        username = f"ada_{uuid.uuid4().hex[:8]}"

        status, created = request_json(
            f"{USER_SERVICE_URL}/users",
            method="POST",
            payload={
                "email": email,
                "username": username,
                "password": "secret",
                "locale": "kk",
            },
        )
        self.assertEqual(status, 201)
        user_id = created["id"]

        status, listed = request_json(f"{USER_SERVICE_URL}/users")
        self.assertEqual(status, 200)
        self.assertTrue(any(item["id"] == user_id for item in listed))

        status, profile = request_json(f"{USER_SERVICE_URL}/users/{user_id}")
        self.assertEqual(status, 200)
        self.assertEqual(profile["email"], email)

        status, updated = request_json(
            f"{USER_SERVICE_URL}/users/{user_id}",
            method="PATCH",
            payload={"username": f"{username}_admin", "locale": "ru"},
        )
        self.assertEqual(status, 200)
        self.assertEqual(updated["locale"], "ru")

        status, _, _ = request(f"{USER_SERVICE_URL}/users/{user_id}/deactivate", method="POST")
        self.assertEqual(status, 204)

        status, _, _ = request(f"{USER_SERVICE_URL}/users/{user_id}/promote", method="POST")
        self.assertEqual(status, 204)

        status, metrics_body, _ = request(f"{USER_SERVICE_URL}/metrics")
        self.assertEqual(status, 200)
        metrics_text = metrics_body.decode("utf-8")
        self.assertIn("http_requests_total", metrics_text)
        self.assertIn('path="/users"', metrics_text)

        wait_until(
            lambda: (
                prometheus_query(
                    'sum(http_requests_total{service="user-service",method="POST",path="/users",status="201"})'
                )
                or 0.0
            )
            >= 1.0,
            message="user-service POST /users metric did not appear in Prometheus",
        )
        wait_until(
            lambda: (
                prometheus_query(
                    f'sum(http_requests_total{{service="user-service",method="GET",path="/users/{user_id}",status="200"}})'
                )
                or 0.0
            )
            >= 1.0,
            message="user-service GET /users/{id} metric did not appear in Prometheus",
        )

    def test_document_service_runtime_and_metrics(self) -> None:
        author_id = str(uuid.uuid4())
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(["name", "amount"])
        writer.writerow(["Alice", "100"])
        writer.writerow(["Bob", "200"])
        body, content_type = build_multipart_form(
            fields={"title": f"Quarterly Report {uuid.uuid4().hex[:6]}", "author_id": author_id},
            files={
                "file": (
                    "report.csv",
                    csv_buffer.getvalue().encode("utf-8"),
                    "text/csv",
                )
            },
        )

        status, raw_created, _ = request(
            f"{DOCUMENT_SERVICE_URL}/documents",
            method="POST",
            headers={"Content-Type": content_type},
            data=body,
        )
        self.assertEqual(status, 201)
        created = json.loads(raw_created.decode("utf-8"))
        document_id = created["id"]

        status, listed = request_json(f"{DOCUMENT_SERVICE_URL}/documents")
        self.assertEqual(status, 200)
        self.assertTrue(any(item["id"] == document_id for item in listed))

        status, fetched = request_json(f"{DOCUMENT_SERVICE_URL}/documents/{document_id}")
        self.assertEqual(status, 200)
        self.assertEqual(fetched["author_id"], author_id)

        status, chunks = request_json(f"{DOCUMENT_SERVICE_URL}/documents/{document_id}/chunks")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(chunks), 1)

        query = urllib.parse.urlencode({"query": "Alice", "limit": 5})
        status, search = request_json(
            f"{DOCUMENT_SERVICE_URL}/documents/{document_id}/chunks/search?{query}"
        )
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(search), 1)

        status, metrics_body, _ = request(f"{DOCUMENT_SERVICE_URL}/metrics")
        self.assertEqual(status, 200)
        metrics_text = metrics_body.decode("utf-8")
        self.assertIn("http_requests_total", metrics_text)
        self.assertIn('path="/documents"', metrics_text)

        wait_until(
            lambda: (
                prometheus_query(
                    'sum(http_requests_total{service="document-service",method="POST",path="/documents",status="201"})'
                )
                or 0.0
            )
            >= 1.0,
            message="document-service POST /documents metric did not appear in Prometheus",
        )
        wait_until(
            lambda: (
                prometheus_query(
                    f'sum(http_requests_total{{service="document-service",method="GET",path="/documents/{document_id}/chunks/search",status="200"}})'
                )
                or 0.0
            )
            >= 1.0,
            message="document-service chunks search metric did not appear in Prometheus",
        )


if __name__ == "__main__":
    unittest.main()
