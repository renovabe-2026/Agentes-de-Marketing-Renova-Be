"""
Cliente Windsor AI para leitura de dados de marketing.
Documentação: https://windsor.ai/api-fields/
"""
import httpx
from datetime import datetime, timedelta
from typing import Optional
import os


WINDSOR_BASE_URL = "https://connectors.windsor.ai"

# Mapeamento de campos por conector
CONNECTOR_FIELDS = {
    "facebook_ads": [
        "campaign_name",
        "date",
        "spend",
        "impressions",
        "clicks",
        "ctr",
        "cpc",
        "conversions",
        "cost_per_conversion",
        "conversion_value",
        "roas",
    ],
    "google_ads": [
        "campaign_name",
        "date",
        "spend",
        "impressions",
        "clicks",
        "ctr",
        "cpc",
        "conversions",
        "cost_per_conversion",
        "conversion_value",
        "roas",
    ],
    "google_analytics4": [
        "date",
        "source",
        "medium",
        "sessions",
        "users",
        "new_users",
        "engaged_sessions",
        "bounce_rate",
        "event_count",
        "conversions",
        "total_revenue",
    ],
    "shopify": [
        "date",
        "orders",
        "revenue",
        "average_order_value",
        "new_customers",
        "returning_customers",
        "total_customers",
    ],
}


class WindsorClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = WINDSOR_BASE_URL
        self.timeout = 30.0

    async def fetch(
        self,
        connector: str,
        date_from: str,
        date_to: str,
        fields: Optional[list] = None,
    ) -> dict:
        """Busca dados de um conector Windsor."""
        if fields is None:
            fields = CONNECTOR_FIELDS.get(connector, [])

        params = {
            "api_key": self.api_key,
            "date_from": date_from,
            "date_to": date_to,
            "fields": ",".join(fields),
            "_renderer": "json",
        }

        url = f"{self.base_url}/{connector}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                # Windsor retorna {"data": [...]} ou lista direta
                if isinstance(data, dict) and "data" in data:
                    return {"success": True, "data": data["data"]}
                elif isinstance(data, list):
                    return {"success": True, "data": data}
                return {"success": True, "data": []}
            except httpx.HTTPStatusError as e:
                return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text}", "data": []}
            except httpx.TimeoutException:
                return {"success": False, "error": "Timeout ao conectar ao Windsor", "data": []}
            except Exception as e:
                return {"success": False, "error": str(e), "data": []}

    async def facebook_ads(self, date_from: str, date_to: str) -> dict:
        return await self.fetch("facebook_ads", date_from, date_to)

    async def google_ads(self, date_from: str, date_to: str) -> dict:
        return await self.fetch("google_ads", date_from, date_to)

    async def ga4(self, date_from: str, date_to: str) -> dict:
        return await self.fetch("google_analytics4", date_from, date_to)

    async def shopify(self, date_from: str, date_to: str) -> dict:
        return await self.fetch("shopify", date_from, date_to)


def get_default_dates(days: int = 30) -> tuple[str, str]:
    """Retorna date_from e date_to para os últimos N dias."""
    today = datetime.today()
    date_to = today.strftime("%Y-%m-%d")
    date_from = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    return date_from, date_to


# ── Funções de Agregação ────────────────────────────────────────────────────

def aggregate_paid_summary(rows: list) -> dict:
    """Agrega métricas de mídia paga (Facebook ou Google) em um sumário."""
    total_spend = 0.0
    total_impressions = 0
    total_clicks = 0
    total_conversions = 0.0
    total_revenue = 0.0

    for row in rows:
        total_spend += float(row.get("spend", 0) or 0)
        total_impressions += int(row.get("impressions", 0) or 0)
        total_clicks += int(row.get("clicks", 0) or 0)
        total_conversions += float(row.get("conversions", 0) or 0)
        total_revenue += float(row.get("conversion_value", 0) or 0)

    ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    cpc = (total_spend / total_clicks) if total_clicks > 0 else 0
    roas = (total_revenue / total_spend) if total_spend > 0 else 0
    cpa = (total_spend / total_conversions) if total_conversions > 0 else 0

    return {
        "spend": round(total_spend, 2),
        "impressions": total_impressions,
        "clicks": total_clicks,
        "conversions": round(total_conversions, 1),
        "revenue": round(total_revenue, 2),
        "ctr": round(ctr, 2),
        "cpc": round(cpc, 2),
        "roas": round(roas, 2),
        "cpa": round(cpa, 2),
    }


def aggregate_campaigns(rows: list) -> list:
    """Agrupa dados por campanha."""
    campaigns: dict = {}
    for row in rows:
        name = row.get("campaign_name", "Sem nome")
        if name not in campaigns:
            campaigns[name] = {
                "campaign_name": name,
                "spend": 0.0,
                "impressions": 0,
                "clicks": 0,
                "conversions": 0.0,
                "revenue": 0.0,
            }
        c = campaigns[name]
        c["spend"] += float(row.get("spend", 0) or 0)
        c["impressions"] += int(row.get("impressions", 0) or 0)
        c["clicks"] += int(row.get("clicks", 0) or 0)
        c["conversions"] += float(row.get("conversions", 0) or 0)
        c["revenue"] += float(row.get("conversion_value", 0) or 0)

    result = []
    for c in campaigns.values():
        c["roas"] = round(c["revenue"] / c["spend"], 2) if c["spend"] > 0 else 0
        c["ctr"] = round(c["clicks"] / c["impressions"] * 100, 2) if c["impressions"] > 0 else 0
        c["spend"] = round(c["spend"], 2)
        c["revenue"] = round(c["revenue"], 2)
        result.append(c)

    return sorted(result, key=lambda x: x["spend"], reverse=True)


def aggregate_ga4_summary(rows: list) -> dict:
    """Agrega dados do GA4."""
    total_sessions = 0
    total_users = 0
    total_new_users = 0
    total_revenue = 0.0
    total_conversions = 0

    for row in rows:
        total_sessions += int(row.get("sessions", 0) or 0)
        total_users += int(row.get("users", 0) or 0)
        total_new_users += int(row.get("new_users", 0) or 0)
        total_revenue += float(row.get("total_revenue", 0) or 0)
        total_conversions += int(row.get("conversions", 0) or 0)

    return {
        "sessions": total_sessions,
        "users": total_users,
        "new_users": total_new_users,
        "revenue": round(total_revenue, 2),
        "conversions": total_conversions,
        "conversion_rate": round(total_conversions / total_sessions * 100, 2) if total_sessions > 0 else 0,
    }


def aggregate_ga4_channels(rows: list) -> list:
    """Agrupa sessões GA4 por canal (source/medium)."""
    channels: dict = {}
    for row in rows:
        source = row.get("source", "(direct)")
        medium = row.get("medium", "(none)")
        key = f"{source} / {medium}"
        if key not in channels:
            channels[key] = {"channel": key, "sessions": 0, "users": 0, "conversions": 0}
        channels[key]["sessions"] += int(row.get("sessions", 0) or 0)
        channels[key]["users"] += int(row.get("users", 0) or 0)
        channels[key]["conversions"] += int(row.get("conversions", 0) or 0)

    return sorted(channels.values(), key=lambda x: x["sessions"], reverse=True)[:10]


def aggregate_shopify_summary(rows: list) -> dict:
    """Agrega dados do Shopify."""
    total_orders = 0
    total_revenue = 0.0
    total_new = 0
    total_returning = 0

    for row in rows:
        total_orders += int(row.get("orders", 0) or 0)
        total_revenue += float(row.get("revenue", 0) or 0)
        total_new += int(row.get("new_customers", 0) or 0)
        total_returning += int(row.get("returning_customers", 0) or 0)

    aov = (total_revenue / total_orders) if total_orders > 0 else 0

    return {
        "orders": total_orders,
        "revenue": round(total_revenue, 2),
        "aov": round(aov, 2),
        "new_customers": total_new,
        "returning_customers": total_returning,
    }


def build_daily_trend(rows: list, value_field: str, date_field: str = "date") -> list:
    """Agrupa valores por data para gráficos de linha."""
    daily: dict = {}
    for row in rows:
        date = row.get(date_field, "")
        if not date:
            continue
        val = float(row.get(value_field, 0) or 0)
        daily[date] = daily.get(date, 0) + val

    return [{"date": k, "value": round(v, 2)} for k, v in sorted(daily.items())]
