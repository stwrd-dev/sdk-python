"""The README examples are code that users copy: they must compile, and the
runnable ones must do what the text says."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from pathlib import Path

import httpx
import pytest

README = Path(__file__).resolve().parent.parent / "README.md"
SIGNING_KEY = "whsec-readme-example"
ENVIRONMENT = {
    "STWRD_ISSUER": "https://idp.example.com",
    "STWRD_CLIENT_ID": "readme-client",
    "STWRD_CLIENT_SECRET": "readme-secret",
    "STWRD_BASE_URL": "https://app.example.com",
    "STWRD_COOKIE_SECRET": "c" * 48,
    "STWRD_WEBHOOK_SECRET": SIGNING_KEY,
}


def _python_blocks(path: Path = README) -> list[tuple[str, str]]:
    """`(heading, code)` for every fenced Python block, in document order."""
    heading = ""
    blocks: list[tuple[str, str]] = []
    inside = False
    code: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not inside:
            if line.startswith("#"):
                heading = line.lstrip("#").strip()
            elif line.startswith("```python"):
                inside, code = True, []
        elif line.startswith("```"):
            blocks.append((heading, "\n".join(code)))
            inside = False
        else:
            code.append(line)
    return blocks


def _block(heading: str) -> str:
    matches = [code for title, code in _python_blocks() if title == heading]
    assert len(matches) == 1, f"expected one Python block under {heading!r}"
    return matches[0]


def _run(heading: str, monkeypatch: pytest.MonkeyPatch) -> dict:
    for name, value in ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    namespace: dict = {"__name__": "readme_example"}
    exec(compile(_block(heading), f"README.md [{heading}]", "exec"), namespace)  # noqa: S102
    return namespace


@pytest.mark.parametrize(
    "heading,code", _python_blocks(), ids=[f"{h}#{i}" for i, (h, _) in enumerate(_python_blocks())]
)
def test_every_python_block_compiles(heading: str, code: str) -> None:
    compile(code, f"README.md [{heading}]", "exec")


GUIDES = sorted((README.parent / "docs").glob("*.md"))
GUIDE_BLOCKS = [(guide.name, code) for guide in GUIDES for _, code in _python_blocks(guide)]


@pytest.mark.parametrize(
    "guide,code", GUIDE_BLOCKS, ids=[f"{g}#{i}" for i, (g, _) in enumerate(GUIDE_BLOCKS)]
)
def test_every_guide_python_block_compiles(guide: str, code: str) -> None:
    compile(code, guide, "exec")


async def _get(app, path: str, **kwargs) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://app.example.com", follow_redirects=False
    ) as client:
        return await client.get(path, **kwargs)


async def test_the_quick_start_app_serves_anonymous_and_protected_routes(monkeypatch) -> None:
    app = _run("Quick start", monkeypatch)["app"]

    home = await _get(app, "/")
    assert home.json() == {"signed_in": False, "sign_in": "/auth/sign-in?return_to=/me"}

    session = await _get(app, "/auth/session")
    assert session.json()["authenticated"] is False
    assert session.json()["account_url"] == "https://idp.example.com/me"

    api_call = await _get(app, "/me", headers={"accept": "application/json"})
    assert api_call.status_code == 401
    navigation = await _get(app, "/me", headers={"accept": "text/html"})
    assert navigation.status_code == 303
    assert navigation.headers["location"].startswith("/auth/sign-in")


async def test_the_roles_example_guards_its_routes(monkeypatch) -> None:
    app = _run("Roles, permissions, sign-out and webhooks", monkeypatch)["app"]

    assert (await _get(app, "/")).status_code == 200
    assert (await _get(app, "/admin", headers={"accept": "application/json"})).status_code == 401
    assert (await _get(app, "/private", headers={"accept": "text/html"})).status_code == 303


def _signature(body: bytes, message_id: str, timestamp: str) -> str:
    digest = hmac.new(
        SIGNING_KEY.encode(), f"{message_id}.{timestamp}.".encode() + body, hashlib.sha256
    ).digest()
    return "v1," + base64.b64encode(digest).decode()


def test_the_framework_free_receiver_verifies_deduplicates_and_rejects(monkeypatch) -> None:
    receive = _run("Without a framework", monkeypatch)["receive"]
    event_id = str(uuid.uuid4())
    timestamp = str(int(time.time()))
    body = json.dumps(
        {
            "id": event_id,
            "type": "user.email_updated",
            "api_version": "v1",
            "created_at": "2026-01-01T00:00:00Z",
            "data": {"user_id": "usr_1"},
        }
    ).encode()
    headers = {
        "webhook-id": event_id,
        "webhook-timestamp": timestamp,
        "webhook-signature": _signature(body, event_id, timestamp),
    }

    assert receive(body, headers) == 200
    assert receive(body, headers) == 200  # duplicate: acknowledged, not reprocessed
    assert receive(body + b" ", headers) == 400
    assert receive(body, {**headers, "webhook-signature": "v1,AAAA"}) == 400
