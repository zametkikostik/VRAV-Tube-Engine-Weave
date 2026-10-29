# YouTube Integration

## Official APIs only

- YouTube Data API v3: https://developers.google.com/youtube/v3  
- Developer Policies: https://developers.google.com/youtube/terms/developer-policies-guide  

**Forbidden:** page scraping, unauthorized media download, fabricated monetization estimates.

## Setup (Google Cloud)

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. Enable **YouTube Data API v3**.
3. Configure OAuth consent screen (External or Internal).
4. Create OAuth 2.0 Client ID (Web application).
5. Add authorized redirect URI, e.g.  
   `https://your.domain/api/v1/integrations/youtube/callback`  
   (local: `http://localhost:8000/api/v1/integrations/youtube/callback`)
6. Put credentials in `.env`:

```
GOOGLE_CLIENT_ID=....apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...
YOUTUBE_REDIRECT_URI=http://localhost:8000/api/v1/integrations/youtube/callback
```

## API flow

1. `GET /api/v1/integrations/youtube/connect` → `authorization_url`
2. User completes Google consent
3. Callback exchanges code; tokens stored **server-side only**
4. `GET /status` / `POST /disconnect`
5. `POST /fetch-metadata` with `{ "youtube_url": "..." }` using Data API

## Quota

Monitor YouTube Data API quota in Google Cloud Console. Cache metadata where appropriate.
