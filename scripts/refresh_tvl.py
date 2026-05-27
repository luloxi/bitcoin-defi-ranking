#!/usr/bin/env python3
"""
refresh_tvl.py — Actualiza TVL desde DeFiLlama API
Usage: python scripts/refresh_tvl.py
Produces: data/ranking.json actualizado + timestamp
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

AR_TZ = timezone(timedelta(hours=-3))
DEFILLAMA_API = "https://api.llama.fi"

# Mapeo de IDs del ranking.json → slugs de DeFiLlama
PROTOCOL_SLUGS = {
    "aave-btc":          "aave",
    "morpho-btc":        "morpho",
    "eigenlayer-btc":    "eigenlayer",
    "pendle-btc":        "pendle",
    "sovryn":            "sovryn",
    "liquidium":         "liquidium",
    # Los siguientes no están en DeFiLlama público — se mantienen valores nulos
    "babylon":           None,
    "core":              None,
    "stacks-sbtc":       None,
    "spark-usdb":        None,
    "bitlayer":          "bitlayer",
    "zest":              None,
    "velar":             None,
}

def fetch_defillama_tvl(slug: str) -> float | None:
    """Trae el TVL actual en USD desde DeFiLlama para un protocolo dado."""
    if slug is None:
        return None
    url = f"{DEFILLAMA_API}/protocol/{slug}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read())
            tvl = data.get("tvl")
            if tvl and tvl > 0:
                return float(tvl)
    except Exception as e:
        print(f"  ⚠ Could not fetch {slug}: {e}", file=sys.stderr)
    return None

def load_data(path: str) -> dict:
    with open(path) as f:
        return json.load(f)

def save_data(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_tvl_display(usd: float | None, btc: float | None) -> str:
    if usd is None and btc is None:
        return "N/D"
    if usd is not None:
        if usd >= 1_000_000_000:
            return f"${usd/1_000_000_000:.1f}B"
        elif usd >= 1_000_000:
            return f"${usd/1_000_000:.0f}M"
        else:
            return f"${usd:,.0f}"
    return "—"

def main():
    base_path = "data/ranking.json"
    now_ar = datetime.now(AR_TZ)
    timestamp = now_ar.strftime("%Y-%m-%dT%H:%M:%S%z")

    print(f"⏳ Refresh TVL — {timestamp}")
    print("─" * 40)

    data = load_data(base_path)
    updated = False

    for p in data["platforms"]:
        slug = PROTOCOL_SLUGS.get(p["id"])
        tvl_usd = None
        if slug:
            print(f"  → {p['id']} ({slug})...", end=" ", flush=True)
            tvl_usd = fetch_defillama_tvl(slug)
            if tvl_usd is not None:
                old = p.get("tvl_usd")
                p["tvl_usd"] = tvl_usd
                p["tvl_display"] = format_tvl_display(tvl_usd, p.get("tvl_btc"))
                print(f"${tvl_usd:,.0f} {'(updated)' if old != tvl_usd else '(unchanged)'}")
                updated = True
            else:
                print("N/D")
        else:
            print(f"  → {p['id']}: no DeFiLlama slug (keeping static data)")

    data["meta"]["updated_at"] = timestamp
    data["meta"]["source"] = (
        f"Research + DeFiLlama live TVL ({timestamp[:-9]} ART). "
        "APY estimates based on Coin Bureau, Messari, Spark, Babylon, DeFiLlama (may 2026)."
    )

    save_data(base_path, data)
    print("─" * 40)
    if updated:
        print("✅ data/ranking.json updated")
    else:
        print("⚠ No changes — DeFiLlama unreachable or all slugs N/D")

if __name__ == "__main__":
    main()