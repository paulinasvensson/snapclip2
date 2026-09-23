"""
snapclip2 - URL shortener with a paid tier.

Free tier: create a short link with an auto-generated code, and use it
(redirects work for anyone).

Paid tier (requires X-License-Key header validated via entitlements.require_pro):
- custom alias/slug for short links
- click analytics (counts + timestamps/referrers)
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

from storage import init_db, create_link, get_link, register_click, get_click_history
from entitlements import require_pro

app = FastAPI(title="snapclip2 - URL Shortener")


@app.on_event("startup")
def on_startup():
    init_db()


class ShortenRequest(BaseModel):
    url: HttpUrl


class ShortenResponse(BaseModel):
    code: str
    short_url: str
    target: str


class CustomShortenRequest(BaseModel):
    url: HttpUrl
    alias: str


@app.post("/shorten", response_model=ShortenResponse)
def shorten(req: ShortenRequest, request: Request):
    """Free tier: shorten a URL with a random auto-generated code."""
    code = create_link(str(req.url))
    base = str(request.base_url).rstrip("/")
    return ShortenResponse(code=code, short_url=f"{base}/{code}", target=str(req.url))


@app.get("/{code}")
def redirect(code: str, request: Request):
    """Free tier: anyone can follow a short link."""
    link = get_link(code)
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    register_click(code, referrer=request.headers.get("referer"))
    return RedirectResponse(url=link["target"])


@app.post("/pro/shorten/custom", response_model=ShortenResponse)
def shorten_custom(
    req: CustomShortenRequest,
    request: Request,
    _license=Depends(require_pro),
):
    """Paid tier: choose your own custom alias/slug."""
    try:
        code = create_link(str(req.url), custom_code=req.alias)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    base = str(request.base_url).rstrip("/")
    return ShortenResponse(code=code, short_url=f"{base}/{code}", target=str(req.url))


@app.get("/pro/analytics/{code}")
def analytics(code: str, _license=Depends(require_pro)):
    """Paid tier: view click analytics for a short link."""
    link = get_link(code)
    if not link:
        raise HTTPException(status_code=404, detail="Short link not found")
    history = get_click_history(code)
    return {
        "code": code,
        "target": link["target"],
        "total_clicks": link["clicks"],
        "created_at": link["created_at"],
        "is_custom": bool(link["is_custom"]),
        "click_history": history,
    }
