# docs.viaduct.dev

This repo builds and deploys [docs.viaduct.dev](https://docs.viaduct.dev) — the public documentation site for [Viaduct](https://github.com/airbnb/viaduct).

[airbnb/viaduct](https://github.com/airbnb/viaduct) is the source of truth. **No content changes are made here.** This repo controls the build, deployment, and any presentation-layer customizations applied on top of the upstream source.

## How it works

Every build follows the same steps, whether local or CI:

1. Clone `airbnb/viaduct` at a specific ref
2. Apply **overlays** from this repo over the cloned source
3. Flatten the `docs/` subdirectory so content is served at clean URLs (e.g. `/developers/` not `/docs/developers/`)
4. Remove non-docs content (about, blog, community, roadmap) so it is never built or indexed
5. Run `mkdocs build` to generate the static site
6. Run Gradle to generate Dokka API references (`/apis/tenant-api/` and `/apis/service/`)
7. Check links with lychee
8. Serve (locally) or deploy to GitHub Pages (CI)

## Overlays

The `overlays/` directory mirrors the upstream file tree. Any file placed here is copied over the upstream checkout before the build runs, replacing the upstream version.

```
overlays/
  docs/
    mkdocs.yml              # nav restructure, site_url, plugin config
    docs/
      index.md              # docs.viaduct.dev root landing page
      kdocs/
        index.md            # KDocs landing page (links to both API references)
```

**To change the nav, site config, or plugins:** edit `overlays/docs/mkdocs.yml`.

**To add or change a page that exists in the upstream:** create a file at the matching path under `overlays/`. It will replace the upstream file at build time.

**To add a new page with no upstream equivalent:** create it under `overlays/` and add it to the nav in `overlays/docs/mkdocs.yml`.

**Things the overlay mkdocs.yml controls:**
- `site_url` — driven by `SITE_URL` env var (set per environment)
- `extra.homepage` — logo links back to `viaduct.airbnb.tech`
- Nav — restructured to Getting Started / Developers / Service Engineers / Contributors / KDocs tabs
- Blog plugin removed (blog content is deleted from the build)

## Local testing

Requires Docker. Builds and serves the site at `http://localhost:8080`:

```bash
cd test && docker compose up --build
```

To build from a specific upstream branch, tag, or commit SHA:

```bash
cd test
SOURCE_REF=v0.28.0 docker compose up --build      # tag
SOURCE_REF=main docker compose up --build         # branch
SOURCE_REF=abc1234ef docker compose up --build    # commit SHA
```

The local build runs the full pipeline: clone, overlay, flatten, delete non-docs, mkdocs build, Dokka. What you see at `localhost:8080` is exactly what deploys to production.

## Link checking

Links are checked with [lychee](https://github.com/lycheeverse/lychee). Exclusions (domains that block bots) are configured in `test/lychee.toml`.

Run the link checker against a running local container:

```bash
cd test
docker compose up --build                                # terminal 1
docker compose --profile linkcheck run --rm linkcheck    # terminal 2
```

In CI, lychee runs automatically after the build and before deployment. A broken link fails the deployment.

To add a link exclusion (e.g. a domain that returns 403 to bots), add a pattern to `test/lychee.toml`.

## CI / deployment

The deploy workflow (`.github/workflows/deploy-docs.yml`) runs on:

- **Push to `main`** — always builds and deploys
- **Weekly schedule** — checks the latest `airbnb/viaduct` SHA; skips if already built for that SHA
- **Manual trigger** — use the **Deploy Docs** workflow from the Actions tab

The pipeline: checkout this repo → checkout `airbnb/viaduct` → apply overlays → flatten → remove non-docs → build → link check → deploy to GitHub Pages.

The upstream SHA cache uses GitHub Actions cache to avoid redundant weekly builds. A push to `main` in this repo always bypasses the cache and deploys unconditionally.

## Switching domains

`SITE_URL` is set in two places and must match:

1. `.github/workflows/deploy-docs.yml` — used in CI builds and the CNAME written to the Pages artifact
2. `test/Dockerfile` default ARG — used for local builds (`http://localhost:8080` by default; override with `SITE_URL=https://... docker compose up`)

DNS and the GitHub Pages custom domain setting (repo Settings → Pages) also need updating when switching domains.
