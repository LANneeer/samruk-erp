from __future__ import annotations

import csv
import io
import json
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any


USER_SERVICE_URL = "http://user-service:8001"
DOCUMENT_GATEWAY_URL = "http://document-gateway:8002"
PROMETHEUS_URL = "http://prometheus:9090"
GRAFANA_URL = "http://grafana:3000"
HTTP_TIMEOUT_SECONDS = 10
WAIT_TIMEOUT_SECONDS = 90
POLL_INTERVAL_SECONDS = 2
SEED_ITERATIONS = 5


def log(message: str) -> None:
    print(f"[mock-e2e] {message}", flush=True)


def request(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_SECONDS) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: Any | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any]:
    body = None
    merged_headers = dict(headers or {})
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        merged_headers["Content-Type"] = "application/json"
    status, raw = request(url, method=method, headers=merged_headers, data=body)
    return status, json.loads(raw.decode("utf-8")) if raw else None


def build_multipart_form(
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
) -> tuple[bytes, str]:
    boundary = f"----mock-e2e-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
                value.encode(),
                b"\r\n",
            ]
        )

    for name, (filename, content, content_type) in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode(),
                (
                    f'Content-Disposition: form-data; name="{name}"; '
                    f'filename="{filename}"\r\n'
                ).encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                content,
                b"\r\n",
            ]
        )

    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def wait_for_http_ok(url: str) -> None:
    deadline = time.time() + WAIT_TIMEOUT_SECONDS
    while time.time() < deadline:
        status, _ = request(url)
        if status == 200:
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    raise RuntimeError(f"{url} did not become ready in time")


def seed_user_service(iteration: int) -> None:
    email = f"seed-{iteration}-{uuid.uuid4().hex[:6]}@example.com"
    username = f"seed_{iteration}_{uuid.uuid4().hex[:6]}"

    status, created = request_json(
        f"{USER_SERVICE_URL}/users",
        method="POST",
        payload={
            "email": email,
            "username": username,
            "password": "secret",
            "locale": "kk" if iteration % 2 == 0 else "ru",
        },
    )
    if status != 201:
        raise RuntimeError(f"user create failed: {status} {created}")

    user_id = created["id"]
    request_json(f"{USER_SERVICE_URL}/users")
    request_json(f"{USER_SERVICE_URL}/users/{user_id}")
    request_json(
        f"{USER_SERVICE_URL}/users/{user_id}",
        method="PATCH",
        payload={"username": f"{username}_upd", "locale": "en"},
    )
    request(f"{USER_SERVICE_URL}/users/{user_id}/deactivate", method="POST")
    request(f"{USER_SERVICE_URL}/users/{user_id}/activate", method="POST")
    request(f"{USER_SERVICE_URL}/users/{user_id}/promote", method="POST")
    request(f"{USER_SERVICE_URL}/metrics")

    # create one conflict metric as well
    request_json(
        f"{USER_SERVICE_URL}/users",
        method="POST",
        payload={
            "email": email,
            "username": f"dup_{iteration}",
            "password": "secret",
            "locale": "en",
        },
    )


def seed_document_gateway(iteration: int) -> None:
    author_id = str(uuid.uuid4())
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["name", "amount", "iteration"])
    writer.writerow(["Alice", "100", str(iteration)])
    writer.writerow(["Bob", "200", str(iteration)])
    writer.writerow(["Carol", "300", str(iteration)])

    title = f"Seed Report {iteration}-{uuid.uuid4().hex[:6]}"
    body, content_type = build_multipart_form(
        fields={},
        files={
            "file": (
                f"seed-{iteration}.csv",
                csv_buffer.getvalue().encode("utf-8"),
                "text/csv",
            )
        },
    )
    create_query = urllib.parse.urlencode({"title": title, "author_id": author_id})

    status, raw = request(
        f"{DOCUMENT_GATEWAY_URL}/documents?{create_query}",
        method="POST",
        headers={"Content-Type": content_type},
        data=body,
    )
    if status != 201:
        raise RuntimeError(f"document create failed: {status} {raw.decode('utf-8', 'ignore')}")

    created = json.loads(raw.decode("utf-8"))
    document_id = created["id"]

    request_json(f"{DOCUMENT_GATEWAY_URL}/documents")
    request_json(f"{DOCUMENT_GATEWAY_URL}/documents/{document_id}")
    request_json(
        f"{DOCUMENT_GATEWAY_URL}/documents/{document_id}",
        method="PATCH",
        payload={"title": f"Updated Seed Report {iteration}"},
    )
    request_json(f"{DOCUMENT_GATEWAY_URL}/documents/{document_id}/chunks")

    for query_text in ("Alice", "Bob", f"iteration {iteration}"):
        query = urllib.parse.urlencode({"query": query_text, "limit": 5})
        request_json(f"{DOCUMENT_GATEWAY_URL}/documents/{document_id}/chunks/search?{query}")

    request(f"{DOCUMENT_GATEWAY_URL}/documents/{document_id}/download")
    request(f"{DOCUMENT_GATEWAY_URL}/metrics")


def touch_observability() -> None:
    request(f"{PROMETHEUS_URL}/-/ready")
    request(f"{PROMETHEUS_URL}/api/v1/query?{urllib.parse.urlencode({'query': 'up'})}")
    request(f"{GRAFANA_URL}/api/health")


def main() -> None:
    log("waiting for user-service")
    wait_for_http_ok(f"{USER_SERVICE_URL}/docs")
    log("waiting for document-gateway")
    wait_for_http_ok(f"{DOCUMENT_GATEWAY_URL}/docs")
    log("waiting for prometheus")
    wait_for_http_ok(f"{PROMETHEUS_URL}/-/ready")
    log("waiting for grafana")
    wait_for_http_ok(f"{GRAFANA_URL}/api/health")

    for iteration in range(1, SEED_ITERATIONS + 1):
        log(f"seeding iteration {iteration}/{SEED_ITERATIONS}")
        seed_user_service(iteration)
        seed_document_gateway(iteration)
        touch_observability()
        time.sleep(1)

    log("mock e2e traffic generation complete")


if __name__ == "__main__":
    main()
