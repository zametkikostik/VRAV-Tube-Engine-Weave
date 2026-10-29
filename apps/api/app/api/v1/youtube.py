"""YouTube OAuth integration — tokens persisted server-side in oauth_tokens."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models.billing import OAuthToken
from app.services.youtube_oauth import (
    build_authorization_url,
    exchange_code_for_tokens,
    fetch_video_metadata,
    new_oauth_state,
    refresh_access_token,
)
from app.utils.youtube import extract_youtube_video_id

router = APIRouter(prefix="/integrations/youtube", tags=["youtube"])

_oauth_states: dict[str, str] = {}


class YouTubeConnectResponse(BaseModel):
    authorization_url: str
    state: str


class YouTubeStatusResponse(BaseModel):
    connected: bool
    has_refresh_token: bool = False
    message: str = ""


@router.get("/connect", response_model=YouTubeConnectResponse)
async def youtube_connect(user: CurrentUser) -> YouTubeConnectResponse:
    try:
        state = new_oauth_state()
        _oauth_states[state] = str(user.id)
        url = build_authorization_url(state=state)
        return YouTubeConnectResponse(authorization_url=url, state=state)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/callback")
async def youtube_callback(
    db: DbSession,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
) -> dict[str, Any]:
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")
    user_id = _oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    try:
        tokens = await exchange_code_for_tokens(code)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    expires_at = None
    if tokens.get("expires_in"):
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(tokens["expires_in"]))

    uid = UUID(user_id)
    existing = await db.scalar(
        select(OAuthToken).where(OAuthToken.user_id == uid, OAuthToken.provider == "youtube")
    )
    if existing:
        existing.access_token = tokens.get("access_token") or existing.access_token
        if tokens.get("refresh_token"):
            existing.refresh_token = tokens["refresh_token"]
        existing.scope = tokens.get("scope")
        existing.expires_at = expires_at
        existing.token_type = tokens.get("token_type") or "Bearer"
    else:
        db.add(
            OAuthToken(
                user_id=uid,
                provider="youtube",
                access_token=tokens.get("access_token") or "",
                refresh_token=tokens.get("refresh_token"),
                scope=tokens.get("scope"),
                expires_at=expires_at,
                token_type=tokens.get("token_type") or "Bearer",
            )
        )
    await db.commit()
    return {
        "status": "connected",
        "user_id": user_id,
        "scope": tokens.get("scope"),
        "note": "Tokens stored server-side only.",
    }


@router.get("/status", response_model=YouTubeStatusResponse)
async def youtube_status(user: CurrentUser, db: DbSession) -> YouTubeStatusResponse:
    tok = await db.scalar(
        select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == "youtube")
    )
    if not tok or not tok.access_token:
        return YouTubeStatusResponse(connected=False, message="Not connected")
    return YouTubeStatusResponse(
        connected=True,
        has_refresh_token=bool(tok.refresh_token),
        message="Connected",
    )


@router.post("/disconnect")
async def youtube_disconnect(user: CurrentUser, db: DbSession) -> dict[str, str]:
    tok = await db.scalar(
        select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == "youtube")
    )
    if tok:
        await db.delete(tok)
        await db.commit()
    return {"status": "disconnected"}


class FetchMetadataRequest(BaseModel):
    youtube_url: str


async def _access_token_for_user(db: DbSession, user_id: UUID) -> str:
    tok = await db.scalar(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "youtube")
    )
    if not tok or not tok.access_token:
        raise HTTPException(status_code=401, detail="YouTube not connected")
    if tok.expires_at and tok.expires_at < datetime.now(timezone.utc) and tok.refresh_token:
        try:
            refreshed = await refresh_access_token(tok.refresh_token)
            tok.access_token = refreshed.get("access_token") or tok.access_token
            if refreshed.get("expires_in"):
                tok.expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=int(refreshed["expires_in"])
                )
            await db.commit()
        except RuntimeError as exc:
            raise HTTPException(status_code=401, detail=f"Token refresh failed: {exc}") from exc
    return tok.access_token


@router.post("/fetch-metadata")
async def fetch_metadata(
    data: FetchMetadataRequest, user: CurrentUser, db: DbSession
) -> dict[str, Any]:
    video_id = extract_youtube_video_id(data.youtube_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    access = await _access_token_for_user(db, user.id)
    try:
        item = await fetch_video_metadata(access, video_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    snippet = item.get("snippet") or {}
    details = item.get("contentDetails") or {}
    return {
        "youtube_video_id": video_id,
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "channel_title": snippet.get("channelTitle"),
        "published_at": snippet.get("publishedAt"),
        "tags": snippet.get("tags"),
        "category_id": snippet.get("categoryId"),
        "duration": details.get("duration"),
        "thumbnails": snippet.get("thumbnails"),
        "source": "youtube_data_api_v3",
    }
