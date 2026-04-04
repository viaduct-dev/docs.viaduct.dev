# docs.viaduct.dev

This repo builds and deploys [docs.viaduct.dev](https://docs.viaduct.dev) — the public documentation site for [Viaduct](https://github.com/airbnb/viaduct).

The site is built from the source at [airbnb/viaduct](https://github.com/airbnb/viaduct). No source changes are made; this repo only controls the build and deployment.

## Stack

- [MkDocs](https://www.mkdocs.org/) with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Dokka](https://kotlinlang.org/docs/dokka-overview.html) for Kotlin API docs
- GitHub Pages for hosting

## Local Development

The `test/` directory contains a Docker-based local preview environment (`Dockerfile`, `docker-compose.yml`, `server.go`) and the shared lychee link-checker config (`lychee.toml`).

Build and serve the site locally at `http://localhost:8080`:

```bash
cd test && docker compose up --build
```

To build from a specific branch, tag, or full commit SHA:

```bash
cd test
SOURCE_REF=v0.28.0 docker compose up --build      # tag
SOURCE_REF=main docker compose up --build          # branch
SOURCE_REF=abc1234ef docker compose up --build     # commit SHA
```

## Link Checking

Links are checked with [lychee](https://github.com/lycheeverse/lychee) — both locally and in CI before every deployment. Exclusions are configured in `test/lychee.toml`.

Run the link checker against the local container (site must be running first):

```bash
cd test
docker compose up --build                                        # terminal 1
docker compose --profile linkcheck run --rm linkcheck           # terminal 2
```

In CI, lychee runs automatically after the build and before the site is pushed to GitHub Pages. A broken link will fail the deployment.

## First-time Setup

Before the first deployment, enable GitHub Pages in the repository settings:

1. Go to **Settings → Pages**
2. Under **Source**, select **GitHub Actions**

This only needs to be done once. Without it, the deploy job will fail with a permissions error.

## Deployment

The site deploys automatically to [docs.viaduct.dev](https://docs.viaduct.dev) via GitHub Actions on every push to `main`. A weekly scheduled run also checks for new commits in [airbnb/viaduct](https://github.com/airbnb/viaduct) and rebuilds only if something has changed.

To trigger a manual deploy, use the **Deploy Docs** workflow from the Actions tab.

## Switching Domains

The canonical domain is set in `.github/workflows/deploy-docs.yml`:

```yaml
env:
  SITE_URL: https://docs.viaduct.dev
```
