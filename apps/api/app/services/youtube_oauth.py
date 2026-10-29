"""YouTube Data API OAuth 2.0 helpers.

Scopes are minimal. Tokens stored server-side only.
Does not scrape YouTube or download protected media.
"""

from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

YOUTUBE_READONLY_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


@dataclass
class YouTubeOAuthConfig:
    client_id: str
    client_secret: str
    redirect_uri: str

    @classmethod
    def from_env(cls) -> "YouTubeOAuthConfig":
        client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
        redirect_uri = os.getenv(
            "YOUTUBE_REDIRECT_URI",
            "http://localhost:8000/api/v1/integrations/youtube/callback",
        )
        if not client_id or not client_secret:
            raise RuntimeError(
                "YouTube OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET "
                "from Google Cloud Console (YouTube Data API v3 enabled)."
            )
        return cls(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri)


def build_authorization_url(*, state: str, scopes: Optional[list[str]] = None) -> str:
    cfg = YouTubeOAuthConfig.from_env()
    scope_list = scopes or [YOUTUBE_READONLY_SCOPE]
    params = {
        "client_id": cfg.client_id,
        "redirect_uri": cfg.redirect_uri,
        "response_type": "code",
        "scope": " ".join(scope_list),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def new_oauth_state() -> str:
    return secrets.token_urlsafe(32)


async def exchange_code_for_tokens(code: str) -> dict[str, Any]:
    cfg = YouTubeOAuthConfig.from_env()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": cfg.client_id,
                "client_secret": cfg.client_secret,
                "redirect_uri": cfg.redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Token exchange failed: {resp.status_code} {resp.text[:300]}")
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    cfg = YouTubeOAuthConfig.from_env()
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": cfg.client_id,
                "client_secret": cfg.client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"Token refresh failed: {resp.status_code} {resp.text[:300]}")
        return resp.json()


async def fetch_video_metadata(access_token: str, video_id: str) -> dict[str, Any]:
    params = {"part": "snippet,contentDetails,status", "id": video_id}
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            YOUTUBE_VIDEOS_URL,
            params=params,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if resp.status_code == 401:
            raise RuntimeError("YouTube access token expired or revoked")
        if resp.status_code == 403:
            raise RuntimeError("YouTube API quota exceeded or permission denied")
        if resp.status_code >= 400:
            raise RuntimeError(f"YouTube API error: {resp.status_code} {resp.text[:300]}")
        data = resp.json()
        items = data.get("items") or []
        if not items:
            raise ValueError("Video not found or not accessible with current permissions")
        return items[0]
