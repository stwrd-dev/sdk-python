"""The signed-in person's own organizations, read with their access token.

`GET {management}/me/memberships` is a self-read: the bearer is the person's
access token and it only ever lists that person's usable memberships for this
application. The destination comes from the issuer's discovery document and is
validated (HTTPS, token endpoint on the issuer origin, audience-consistent;
the account host may legitimately differ from a custom login domain) before any token is
sent; redirects are never followed with the token.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

import httpx

from .management import ManagementProtocolError, validate_management_discovery
from .oidc import Discovery, IdpUnavailable

MAX_PAGES = 50


@dataclass(frozen=True)
class OwnOrganization:
    id: str
    display_name: str | None


async def list_own_organizations(
    http: httpx.AsyncClient, issuer: str, discovery: Discovery, access_token: str
) -> list[OwnOrganization]:
    try:
        destination = validate_management_discovery(issuer, dict(discovery.document))
    except ManagementProtocolError as exc:
        raise IdpUnavailable(f"Management destination rejected: {exc}") from exc
    found: dict[str, OwnOrganization] = {}
    seen_cursors: set[str] = set()
    cursor: str | None = None
    for _ in range(MAX_PAGES):
        params: dict[str, Any] = {"limit": 200}
        if cursor:
            params["cursor"] = cursor
        try:
            response = await http.request(
                "GET",
                f"{destination.base_url}/me/memberships",
                params=params,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                follow_redirects=False,
            )
        except httpx.HTTPError as exc:
            raise IdpUnavailable(
                f"Memberships: the IdP did not respond ({type(exc).__name__})."
            ) from exc
        if response.status_code != 200:
            raise IdpUnavailable(f"Memberships: the IdP responded {response.status_code}.")
        try:
            body = response.json()
            items = body["items"]
            next_cursor = body["page"]["next_cursor"]
            for item in items:
                if item["active"] is not True:
                    continue
                identifier = str(uuid.UUID(item["organization"]["id"]))
                name = item["organization"]["display_name"]
                found[identifier] = OwnOrganization(
                    identifier, name if isinstance(name, str) else None
                )
        except (ValueError, KeyError, TypeError, AttributeError) as exc:
            raise IdpUnavailable("Memberships: unreadable response.") from exc
        if next_cursor is None:
            return list(found.values())
        if not isinstance(next_cursor, str) or not next_cursor or next_cursor in seen_cursors:
            raise IdpUnavailable("Memberships: repeated or invalid cursor.")
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    raise IdpUnavailable("Memberships: too many pages.")
