# snapclip2

A minimal URL shortener with a paid tier, built for live-deploy-verification-3.

## Features

### Free tier (no license required)
- `POST /shorten` — shorten any URL, get a random 6-character short code.
- `GET /{code}` — follow a short link (redirects to the original URL, tracks the click).

### Paid tier (requires `X-License-Key` header)
- `POST /pro/shorten/custom` — create a short link with your own custom alias.
- `GET /pro/analytics/{code}` — view total clicks and click history (timestamps + referrers) for a link.

Paid endpoints are gated by `entitlements.require_pro`, which checks the
`X-License-Key` header against a license registry (`licenses.json` by default,
or a single `DEMO_PRO_KEY` env var for quick testing).

## Run locally

