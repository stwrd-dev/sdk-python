"""Compile and execute generated bindings from representative OpenAPI contracts."""

from __future__ import annotations

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_management.py"


def ref(name):
    return {"$ref": "#/components/schemas/" + name}


def response(schema, media="application/json"):
    return {"200": {"content": {media: {"schema": schema}}}}


def parameter(name, location="path", required=True, schema=None):
    return {
        "name": name,
        "in": location,
        "required": required,
        "schema": schema or {"type": "string"},
    }


def document():
    page = {
        "type": "object",
        "required": ["next_cursor"],
        "properties": {"next_cursor": {"anyOf": [{"type": "string"}, {"type": "null"}]}},
    }
    person = {
        "type": "object",
        "required": ["id", "display_name"],
        "properties": {
            "id": {"type": "string", "format": "uuid"},
            "display_name": {"type": "string"},
            "metadata": {"type": "object", "additionalProperties": {"type": "string"}},
        },
    }
    version = {
        "type": "object",
        "required": ["consent_id", "version"],
        "properties": {"consent_id": {"type": "string"}, "version": {"type": "integer"}},
    }
    channel = {
        "type": "object",
        "required": ["channel"],
        "properties": {"channel": {"enum": ["email", "sms"]}},
    }
    schemas = {
        "Page": page,
        "Person": person,
        "Version": version,
        "Channel": channel,
        "DecoratedPerson": {
            "allOf": [
                ref("Person"),
                {
                    "type": "object",
                    "required": ["enabled"],
                    "properties": {"enabled": {"type": "boolean"}},
                },
            ]
        },
        "Tree": {
            "type": "object",
            "properties": {
                "child": {"anyOf": [ref("Tree"), {"type": "null"}]},
                "x-label": {"type": "string"},
            },
        },
        "Upload": {
            "type": "object",
            "required": ["document"],
            "properties": {
                "document": {"type": "string", "format": "binary"},
                "label": {"type": "string"},
            },
        },
    }
    for name, item in [("People", "Person"), ("Versions", "Version"), ("Channels", "Channel")]:
        schemas[name] = {
            "type": "object",
            "required": ["items", "page"],
            "properties": {"items": {"type": "array", "items": ref(item)}, "page": ref("Page")},
        }
    query = [
        parameter("cursor", "query", False),
        parameter("q", "query", False, {"anyOf": [{"type": "string"}, {"type": "null"}]}),
        parameter("roles", "query", False, {"type": "array", "items": {"type": "string"}}),
    ]
    return {
        "openapi": "3.1.0",
        "components": {"schemas": schemas},
        "paths": {
            "/api/v1/users": {
                "get": {
                    "operationId": "list_users",
                    "parameters": query,
                    "responses": response(ref("People")),
                }
            },
            "/api/v1/users/{user_id}": {
                "parameters": [parameter("user_id")],
                "get": {"operationId": "get_user", "responses": response(ref("Person"))},
                "patch": {
                    "operationId": "update_user",
                    "parameters": [
                        parameter("If-Match", "header"),
                        parameter("Idempotency-Key", "header"),
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": ref("Person")}},
                    },
                    "responses": response(ref("Person")),
                },
            },
            "/api/v1/applications/{application_id}/consents/{consent_id}/versions": {
                "parameters": [parameter("application_id"), parameter("consent_id")],
                "get": {
                    "operationId": "list_versions",
                    "parameters": query,
                    "responses": response(ref("Versions")),
                },
                "post": {
                    "operationId": "publish_version",
                    "parameters": [
                        parameter("If-Match", "header"),
                        parameter("Idempotency-Key", "header"),
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {"multipart/form-data": {"schema": ref("Upload")}},
                    },
                    "responses": response(ref("Version")),
                },
            },
            "/api/v1/applications/{application_id}/channels": {
                "parameters": [parameter("application_id")],
                "get": {
                    "operationId": "list_channels",
                    "parameters": [parameter("cursor", "query", False)],
                    "responses": response(ref("Channels")),
                },
            },
            "/api/v1/consent-documents/{digest}": {
                "parameters": [parameter("digest")],
                "get": {
                    "operationId": "download_document",
                    "responses": response(
                        {"type": "string", "format": "binary"}, "application/pdf"
                    ),
                },
            },
        },
    }


@pytest.fixture
def generated(tmp_path, monkeypatch):
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps(document()))
    package = tmp_path / "generated_sdk"
    package.mkdir()
    (package / "__init__.py").write_text("")
    shutil.copy(ROOT / "stwrd" / "management.py", package / "management.py")
    output = package / "management_generated.py"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(schema), str(output)], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    monkeypatch.syspath_prepend(str(tmp_path))
    for name in list(sys.modules):
        if name == "generated_sdk" or name.startswith("generated_sdk."):
            del sys.modules[name]
    module = importlib.import_module("generated_sdk.management_generated")
    yield module, tmp_path, output
    for name in list(sys.modules):
        if name == "generated_sdk" or name.startswith("generated_sdk."):
            del sys.modules[name]


def mypy(path, cwd):
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "mypy",
            "--ignore-missing-imports",
            "--follow-imports=silent",
            str(path),
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_every_operation_and_nested_iterator_compiles_with_required_contract(generated):
    module, directory, output = generated
    result = mypy(output, directory)
    assert result.returncode == 0, result.stdout + result.stderr
    expected = {
        op["operationId"]
        for item in document()["paths"].values()
        for op in item.values()
        if isinstance(op, dict) and "operationId" in op
    }
    assert {
        name
        for name in vars(module.ManagementOperations)
        if not name.startswith("_") and not name.endswith("_iterate")
    } == expected
    consumer = directory / "consumer.py"
    consumer.write_text("""from generated_sdk.management import ManagementOptions
from generated_sdk.management_generated import create_management, UpdateUserWriteOptions
client = create_management(ManagementOptions("https://login.test", "service", "secret"))
async def use() -> None:
    result = await client.users.get(user_id="person")
    reveal_type(result.data)
    await client.users.update(
        user_id="person", body={"id": "person", "display_name": "Chosen"},
        options=UpdateUserWriteOptions(if_match="v1", idempotency_key="intent"))
    async for version in client.applications.consents.versions.iterate(
        application_id="app", consent_id="term", query={"q": None, "roles": ["a", "b"]},
        identity=lambda item: str(item["version"])):
        reveal_type(version)
    async for channel in client.applications.channels.iterate(
        application_id="app", identity=lambda item: item["channel"]):
        reveal_type(channel)
""")
    result = mypy(consumer, directory)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Person" in result.stdout and "Version" in result.stdout and "Channel" in result.stdout
    consumer.write_text("""from generated_sdk.management import ManagementOptions
from generated_sdk.management_generated import create_management, UpdateUserWriteOptions
client = create_management(ManagementOptions("https://login.test", "service", "secret"))
async def invalid() -> None:
    await client.users.update(user_id="person", body={"id":"person", "display_name":"Name"})
    UpdateUserWriteOptions(if_match="v1")
    client.applications.channels.iterate(application_id="app")
""")
    result = mypy(consumer, directory)
    assert result.returncode != 0
    assert (
        '"options"' in result.stdout
        and '"idempotency_key"' in result.stdout
        and '"identity"' in result.stdout
    )


async def test_generated_calls_preserve_paths_queries_metadata_headers_and_upload_bytes(generated):
    module, _, _ = generated
    requests = []

    async def handle(request):
        requests.append(request)
        if request.url.path.endswith("openid-configuration"):
            return httpx.Response(
                200,
                json={
                    "issuer": "https://login.test",
                    "token_endpoint": "https://login.test/token",
                    "management_api_base_url": "https://account.test/api/v1",
                    "management_api_audience": "https://account.test",
                },
            )
        if request.url.path == "/token":
            return httpx.Response(
                200,
                json={"access_token": "service-token", "token_type": "Bearer", "expires_in": 3600},
            )
        if request.url.path.startswith("/api/v1/consent-documents/"):
            return httpx.Response(200, content=b"%PDF-real-bytes", headers={"ETag": '"pdf"'})
        if request.url.path.endswith("/versions"):
            return httpx.Response(
                200,
                json={"consent_id": "term", "version": 1},
                headers={"ETag": '"v2"', "X-Request-ID": "request"},
            )
        return httpx.Response(
            200,
            json={"id": "person", "display_name": "Chosen"},
            headers={"ETag": '"v2"', "X-Request-ID": "request"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        options = module.ManagementOptions("https://login.test", "service", "secret")
        async with module.create_management(options, http_client=http) as client:
            result = await client.users.update(
                user_id="person",
                body={"id": "person", "display_name": "Chosen"},
                options=module.UpdateUserWriteOptions(
                    if_match='"v1"',
                    idempotency_key="intent",
                    confirmation_token="confirm",
                    step_up_token="step",
                ),
            )
            assert result.etag == '"v2"' and result.request_id == "request"
            await client.operations.list_users(query={"q": None, "roles": ["a", "b"]})
            data = await client.applications.consents.versions.create(
                application_id="app",
                consent_id="term",
                body=module.MultipartInput(
                    {"label": "Legal"}, {"document": ("legal.pdf", b"PDF", "application/pdf")}
                ),
                options=module.PublishVersionWriteOptions(
                    if_match='"v1"', idempotency_key="publish"
                ),
            )
            assert data.etag == '"v2"'
            pdf = await client.consent_documents.get(digest="digest")
            assert pdf.data == b"%PDF-real-bytes" and pdf.etag == '"pdf"'
    update = next(request for request in requests if request.method == "PATCH")
    assert update.url.path == "/api/v1/users/person"
    assert [
        update.headers[key]
        for key in ("If-Match", "Idempotency-Key", "Confirmation-Token", "X-Stwrd-Step-Up")
    ] == ['"v1"', "intent", "confirm", "step"]
    query = next(request for request in requests if request.url.path == "/api/v1/users")
    assert query.url.params.multi_items() == [("roles", "a"), ("roles", "b")]
    upload = next(request for request in requests if request.url.path.endswith("/versions"))
    assert b'filename="legal.pdf"' in upload.content and b"PDF" in upload.content
    assert upload.headers["Content-Type"].startswith("multipart/form-data; boundary=")


async def test_all_paged_resources_iterate_with_schema_identity_or_explicit_callback(generated):
    module, _, _ = generated
    calls = []

    async def handle(request):
        if request.url.path.endswith("openid-configuration"):
            return httpx.Response(
                200,
                json={
                    "issuer": "https://login.test",
                    "token_endpoint": "https://login.test/token",
                    "management_api_base_url": "https://account.test/api/v1",
                    "management_api_audience": "https://account.test",
                },
            )
        if request.url.path == "/token":
            return httpx.Response(
                200, json={"access_token": "token", "token_type": "Bearer", "expires_in": 3600}
            )
        calls.append(request)
        if request.url.path.endswith("versions"):
            item = {"consent_id": "term", "version": 2 if "cursor" in request.url.params else 1}
        elif request.url.path.endswith("channels"):
            item = {"channel": "sms" if "cursor" in request.url.params else "email"}
        else:
            item = {
                "id": "second" if "cursor" in request.url.params else "first",
                "display_name": "Person",
            }
        return httpx.Response(
            200,
            json={
                "items": [item],
                "page": {"next_cursor": None if "cursor" in request.url.params else "next"},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
        async with module.create_management(
            module.ManagementOptions("https://login.test", "service", "secret"), http_client=http
        ) as client:
            people = [row async for row in client.users.iterate()]
            versions = [
                row
                async for row in client.applications.consents.versions.iterate(
                    application_id="app", consent_id="term", identity=lambda row: row["version"]
                )
            ]
            channels = [
                row
                async for row in client.applications.channels.iterate(
                    application_id="app", identity=lambda row: row["channel"]
                )
            ]
    assert [row["id"] for row in people] == ["first", "second"]
    assert [row["version"] for row in versions] == [1, 2]
    assert [row["channel"] for row in channels] == ["email", "sms"]
    assert len(calls) == 6


@pytest.mark.parametrize(
    "fault", ["private", "duplicate", "missing_operation", "required_unknown_header"]
)
def test_invalid_schema_fails_before_overwriting_output(tmp_path, fault):
    schema = document()
    if fault == "private":
        schema["paths"]["/internal/v1/users"] = schema["paths"].pop("/api/v1/users")
    elif fault == "duplicate":
        schema["paths"]["/api/v1/users"]["get"]["operationId"] = "get_user"
    elif fault == "missing_operation":
        del schema["paths"]["/api/v1/users"]["get"]["operationId"]
    else:
        schema["paths"]["/api/v1/users"]["get"]["parameters"].append(
            parameter("X-Unknown", "header")
        )
    source = tmp_path / "schema.json"
    source.write_text(json.dumps(schema))
    output = tmp_path / "generated.py"
    output.write_text("unchanged")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(source), str(output)], capture_output=True
    )
    assert result.returncode != 0 and output.read_text() == "unchanged"
