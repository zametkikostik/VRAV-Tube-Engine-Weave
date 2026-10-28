# Finish repository sync

Part of the tree is already on GitHub (`main`). Remaining application sources
are in the local monorepo / release tarball.

## Fastest path (recommended)

```bash
# From the full local project directory:
export GITHUB_TOKEN=ghp_your_token_with_repo_scope

git remote set-url origin https://x-access-token:${GITHUB_TOKEN}@github.com/zametkikostik/VRAV-Tube-Engine-Weave.git
git push -u origin main --force-with-lease
git push origin v0.1.0-beta
```

Or download the source tarball produced during development and extract over a clone,
then commit and push.

## After full tree is on main

1. GitHub → Releases → Draft release → tag `v0.1.0-beta`
2. Publish → **Release** workflow attaches zip/tar.gz assets automatically
