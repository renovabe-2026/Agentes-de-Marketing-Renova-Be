"""
Dashboard de Marketing Renova Be
Rode com: uvicorn dashboard.app:app --host 0.0.0.0 --port 8000 --reload
"""
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from dashboard.windsor_client import (
    WindsorClient,
    get_default_dates,
    aggregate_paid_summary,
    aggregate_campaigns,
    aggregate_ga4_summary,
    aggregate_ga4_channels,
    aggregate_shopify_summary,
    build_daily_trend,
)

load_dotenv()

WINDSOR_API_KEY = os.getenv("WINDSOR_API_KEY", "")

app = FastAPI(title="Renova Be – Dashboard de Marketing", docs_url=None, redoc_url=None)

BASE_DIR = os.path.dirname(__file__)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


def _client() -> WindsorClient:
    return WindsorClient(WINDSOR_API_KEY)


def _parse_dates(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    days: int = 30,
) -> tuple[str, str]:
    if date_from and date_to:
        return date_from, date_to
    return get_default_dates(days)


# ── Página Principal ────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ── Endpoints de Dados ──────────────────────────────────────────────────────

@app.get("/api/overview")
async def api_overview(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    days: int = Query(30),
):
    """KPIs gerais: spend total, receita, ROAS, pedidos, sessões."""
    df, dt = _parse_dates(date_from, date_to, days)
    client = _client()

    fb_data, gg_data, shopify_data, ga4_data = await _fetch_all(client, df, dt)

    fb_summary = aggregate_paid_summary(fb_data.get("data", []))
    gg_summary = aggregate_paid_summary(gg_data.get("data", []))
    shopify_summary = aggregate_shopify_summary(shopify_data.get("data", []))
    ga4_summary = aggregate_ga4_summary(ga4_data.get("data", []))

    total_spend = fb_summary["spend"] + gg_summary["spend"]
    total_revenue = shopify_summary["revenue"]
    total_roas = round(total_revenue / total_spend, 2) if total_spend > 0 else 0

    return {
        "period": {"from": df, "to": dt, "days": days},
        "overview": {
            "total_spend": total_spend,
            "total_revenue": total_revenue,
            "total_roas": total_roas,
            "total_orders": shopify_summary["orders"],
            "aov": shopify_summary["aov"],
            "sessions": ga4_summary["sessions"],
            "new_users": ga4_summary["new_users"],
            "cac": round(total_spend / shopify_summary["orders"], 2) if shopify_summary["orders"] > 0 else 0,
        },
        "facebook": fb_summary,
        "google": gg_summary,
        "shopify": shopify_summary,
        "ga4": ga4_summary,
        "errors": _collect_errors(fb_data, gg_data, shopify_data, ga4_data),
    }


@app.get("/api/facebook")
async def api_facebook(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    days: int = Query(30),
):
    df, dt = _parse_dates(date_from, date_to, days)
    data = await _client().facebook_ads(df, dt)
    rows = data.get("data", [])
    return {
        "success": data.get("success", False),
        "error": data.get("error"),
        "summary": aggregate_paid_summary(rows),
        "campaigns": aggregate_campaigns(rows),
        "daily_spend": build_daily_trend(rows, "spend"),
        "daily_revenue": build_daily_trend(rows, "conversion_value"),
    }


@app.get("/api/google")
async def api_google(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    days: int = Query(30),
):
    df, dt = _parse_dates(date_from, date_to, days)
    data = await _client().google_ads(df, dt)
    rows = data.get("data", [])
    return {
        "success": data.get("success", False),
        "error": data.get("error"),
        "summary": aggregate_paid_summary(rows),
        "campaigns": aggregate_campaigns(rows),
        "daily_spend": build_daily_trend(rows, "spend"),
        "daily_revenue": build_daily_trend(rows, "conversion_value"),
    }


@app.get("/api/ga4")
async def api_ga4(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    days: int = Query(30),
):
    df, dt = _parse_dates(date_from, date_to, days)
    data = await _client().ga4(df, dt)
    rows = data.get("data", [])
    return {
        "success": data.get("success", False),
        "error": data.get("error"),
        "summary": aggregate_ga4_summary(rows),
        "channels": aggregate_ga4_channels(rows),
        "daily_sessions": build_daily_trend(rows, "sessions"),
    }


@app.get("/api/shopify")
async def api_shopify(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    days: int = Query(30),
):
    df, dt = _parse_dates(date_from, date_to, days)
    data = await _client().shopify(df, dt)
    rows = data.get("data", [])
    return {
        "success": data.get("success", False),
        "error": data.get("error"),
        "summary": aggregate_shopify_summary(rows),
        "daily_revenue": build_daily_trend(rows, "revenue"),
        "daily_orders": build_daily_trend(rows, "orders"),
    }


# ── Helpers Internos ────────────────────────────────────────────────────────

async def _fetch_all(client: WindsorClient, df: str, dt: str):
    import asyncio
    fb, gg, sh, ga = await asyncio.gather(
        client.facebook_ads(df, dt),
        client.google_ads(df, dt),
        client.shopify(df, dt),
        client.ga4(df, dt),
    )
    return fb, gg, sh, ga


def _collect_errors(*results) -> list:
    errors = []
    labels = ["Facebook Ads", "Google Ads", "Shopify", "GA4"]
    for label, r in zip(labels, results):
        if not r.get("success", True) or r.get("error"):
            errors.append({"source": label, "message": r.get("error", "Erro desconhecido")})
    return errors
