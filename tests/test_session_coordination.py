"""Refresh must survive concurrent BFF workers, lost responses and logout."""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace

import httpx
import pytest

from stwrd import IdpUnavailable, Stwrd

from .test_refresh import _log_in_with_refresh


def is_refresh(request: httpx.Request) -> bool:
    return request.url.path == "/oidc/token" and b"grant_type=refresh_token" in request.content


async def test_two_instances_exchange_a_single_use_refresh_at_most_once(
    stwrd, stwrd_config, idp_http_client, fake_idp
):
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    peer = Stwrd(stwrd_config, http_client=idp_http_client, sessions=stwrd.sessions)
    entered = asyncio.Event()
    release = asyncio.Event()
    requests = []

    async def delay(request):
        if is_refresh(request):
            requests.append(request)
            entered.set()
            await release.wait()

    idp_http_client.event_hooks["request"].append(delay)
    cookie = stwrd.seal({"sid": session.id})
    first = asyncio.create_task(stwrd.resolve_session(cookie))
    await asyncio.wait_for(entered.wait(), 3)
    second = asyncio.create_task(peer.resolve_session(cookie))
    deadline = time.monotonic() + 3
    while len(requests) == 1 and not second.done() and time.monotonic() < deadline:
        await asyncio.sleep(0.01)
    release.set()
    results = await asyncio.gather(first, second, return_exceptions=True)
    assert len(fake_idp.refresh_calls) == 1
    assert all(result is not None for result in results)
    assert all(
        not isinstance(result, Exception) or isinstance(result, IdpUnavailable)
        for result in results
    )
    stored = await stwrd.sessions.get(session.id)
    assert stored is not None
    assert stored.tokens.refresh_token != session.tokens.refresh_token
    assert await peer.resolve_session(cookie) is not None


async def test_logout_during_refresh_cannot_resurrect_the_deleted_session(
    stwrd, idp_http_client, fake_idp
):
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    entered = asyncio.Event()
    release = asyncio.Event()

    async def delay(request):
        if is_refresh(request):
            entered.set()
            await release.wait()

    idp_http_client.event_hooks["request"].append(delay)
    pending = asyncio.create_task(stwrd.resolve_session(stwrd.seal({"sid": session.id})))
    await asyncio.wait_for(entered.wait(), 3)
    await stwrd.sessions.delete(session.id)
    release.set()
    await asyncio.gather(pending, return_exceptions=True)
    assert len(fake_idp.refresh_calls) == 1
    assert await stwrd.sessions.get(session.id) is None


async def test_lost_response_after_rotation_never_replays_the_consumed_refresh(
    stwrd, idp_http_client, fake_idp
):
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    raised = False

    async def lose_response(response):
        nonlocal raised
        if is_refresh(response.request) and not raised:
            raised = True
            raise httpx.ReadError("response lost after processing", request=response.request)

    idp_http_client.event_hooks["response"].append(lose_response)
    cookie = stwrd.seal({"sid": session.id})
    with pytest.raises(IdpUnavailable):
        await stwrd.resolve_session(cookie)
    with pytest.raises(IdpUnavailable):
        await stwrd.resolve_session(cookie)
    assert len(fake_idp.refresh_calls) == 1
    assert await stwrd.sessions.get(session.id) is not None


async def test_userinfo_recovery_uses_checkpointed_tokens_without_another_rotation(
    stwrd, idp_http_client, fake_idp
):
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    failed = False

    async def lose_userinfo(response):
        nonlocal failed
        if response.request.url.path == "/oidc/userinfo" and not failed:
            failed = True
            raise httpx.ReadError("userinfo temporarily unavailable", request=response.request)

    idp_http_client.event_hooks["response"].append(lose_userinfo)
    cookie = stwrd.seal({"sid": session.id})
    with pytest.raises(IdpUnavailable):
        await stwrd.resolve_session(cookie)
    restored = await stwrd.resolve_session(cookie)
    assert restored is not None
    assert len(fake_idp.refresh_calls) == 1
    assert not restored.access_token_expired()


async def test_a_lost_lease_never_deletes_a_recreated_session(stwrd, idp_http_client, fake_idp):
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    entered = asyncio.Event()
    release = asyncio.Event()

    async def delay(request):
        if is_refresh(request):
            entered.set()
            await release.wait()

    idp_http_client.event_hooks["request"].append(delay)
    pending = asyncio.create_task(stwrd.resolve_session(stwrd.seal({"sid": session.id})))
    await asyncio.wait_for(entered.wait(), 3)
    await stwrd.sessions.set(session)  # the person signed in again with the same sid
    release.set()
    with pytest.raises(IdpUnavailable):
        await pending
    assert await stwrd.sessions.get(session.id) is not None


async def _uncertain_session(store, session):
    """A lease that expired in phase `sent` and was seen `uncertain` by a second claimer."""
    await store.set(session)
    first = await store.claim_refresh(session.id, "a", 0.05)
    assert first.status == "granted"
    assert await store.mark_refresh_sent(session.id, first.fence)
    await asyncio.sleep(0.15)
    assert (await store.claim_refresh(session.id, "b", 30)).status == "uncertain"
    return first.fence


async def test_a_late_release_of_the_owner_never_reopens_an_uncertain_session(stwrd, fake_idp):
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    fence = await _uncertain_session(stwrd.sessions, session)
    await stwrd.sessions.release_refresh(session.id, fence, sent=True)
    assert (await stwrd.sessions.claim_refresh(session.id, "c", 30)).status == "uncertain"
    await stwrd.sessions.release_refresh(session.id, fence, sent=False)  # even "nothing was sent"
    assert (await stwrd.sessions.claim_refresh(session.id, "d", 30)).status == "uncertain"


async def test_a_late_owner_cannot_complete_the_refresh_of_an_uncertain_session(stwrd, fake_idp):
    session = await _log_in_with_refresh(stwrd, fake_idp, access_expires_in=-1)
    fence = await _uncertain_session(stwrd.sessions, session)
    late = replace(session, claims={**session.claims, "name": "late"})
    assert await stwrd.sessions.complete_refresh(session.id, fence, late) is False
    stored = await stwrd.sessions.get(session.id)
    assert stored is not None and stored.claims == session.claims
    assert (await stwrd.sessions.claim_refresh(session.id, "c", 30)).status == "uncertain"
