# Releasing

## One-command style

```bash
git checkout main
git pull
git tag -a v0.1.0-beta -m "VRAV Tube Engine commercial beta"
git push origin main
git push origin v0.1.0-beta
```

GitHub Action **Release** builds and uploads assets automatically.

## Via GitHub UI

1. Releases → **Draft a new release**
2. Choose tag `v0.1.0-beta` (or create)
3. Title: `VRAV Tube Engine v0.1.0-beta`
4. Description: paste from `docs/RELEASE_NOTES_v0.1.0-beta.md`
5. Mark as **pre-release** for beta
6. **Publish release** → workflow attaches zip/tar.gz + SHA256SUMS

## Assets explained

- **source** — audit / self-host from source
- **web-dist** — drop into Nginx/Caddy `root`
- **deploy-bundle** — ops files only
- **SHA256SUMS** — verify downloads

`GITHUB_TOKEN` is provided by Actions; no extra secret required for public/private repos with default permissions.
