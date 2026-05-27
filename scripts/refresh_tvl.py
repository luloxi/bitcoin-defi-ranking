#!/usr/bin/env python3
"""
refresh_tvl.py — Actualiza TVL desde DeFiLlama API para todos los protocolos del ranking.
Usage: python scripts/refresh_tvl.py
"""
import json, sys, urllib.request
from datetime import datetime, timezone, timedelta

AR_TZ = timezone(timedelta(hours=-3))
BASE_URL = "https://api.llama.fi"

# slug → DeFiLlama protocol slug
PROTOCOL_SLUGS = {
    "aave-btc":         "aave",
    "morpho-btc":       "morpho",
    "eigenlayer-btc":   "eigenlayer",
    "pendle-btc":       "pendle",
    "sovryn":           "sovryn",
    "liquidium":        "liquidium",
    "bitlayer":         "bitlayer",
    "yearn-btc":        "yearn-finance",
    "beefy-btc":        "beefy",
    "element-btc":      "element-finance",
    "curve-btc":        "curve-dao",
    "uniswap-btc":      "uniswap",
    "uniswap-bitcoin-l2":"uniswap",
    "euler-btc":        "euler",
    "gearbox-btc":      "gearbox-protocol",
    "cream-btc":        "cream-finance",
    "revert-btc":       "revert-finance",
    "instadapp-btc":    "instadapp",
    "maple-btc":        "maple-finance",
    "solana-btc-dex":   None,      # Solana — DeFiLlama no tiene slug preciso
    "raydium-btc":      "raydium",
    "stride-btc":       "stride",
    "pstake-btc":       "pstake-finance",
    "alex-btc":         "alex-lab",
    "lava":             None,      # Pivot a custodial — no en DeFiLlama
    # Non-DeFiLlama (static only):
    "babylon":          None,
    "core":             None,
    "stacks-sbtc":      None,
    "zest":             None,
    "velar":            None,
    "spark-usdb":       None,
    "botanix":          None,
    "citrea":           None,
    "solvbtc":          None,
    "stbtc":            None,
    "cardano-lsd":      None,
    "ardolik":          None,
    "sundaeswap-btc":   None,
    "minswap-btc":      None,
    "bisq":             None,
    "robosats":         None,
    "liquid-rwa":       None,
    "compound-btc":     "compound",
}

def fetch_tvl(slug: str) -> float | None:
    if not slug:
        return None
    try:
        url = f"{BASE_URL}/protocol/{slug}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            tvl = data.get("tvl")
            if tvl and isinstance(tvl, (int, float)) and tvl > 0:
                return float(tvl)
    except Exception as e:
        print(f"  ⚠ {slug}: {e}", file=sys.stderr)
    return None

def fmt(usd: float) -> str:
    if usd >= 1e9:  return f"${usd/1e9:.1f}B"
    if usd >= 1e6: return f"${usd/1e6:.0f}M"
    return f"${usd:,.0f}"

def main():
    print(f"⏳ Refresh TVL — {datetime.now(AR_TZ):%Y-%m-%d %H:%M ART}")
    print("─" * 44)

    with open("data/ranking.json") as f:
        data = json.load(f)

    updated = 0
    for p in data["platforms"]:
        slug = PROTOCOL_SLUGS.get(p["id"])
        if not slug:
            print(f"  ─ {p['id']}: no DeFiLlama slug (static)")
            continue
        print(f"  → {p['id']} ({slug})...", end=" ", flush=True)
        new_tvl = fetch_tvl(slug)
        if new_tvl is not None:
            old = p.get("tvl_usd")
            p["tvl_usd"] = new_tvl
            p["tvl_display"] = fmt(new_tvl)
            changed = (old is None) or (abs(new_tvl - old) / old > 0.001) if old else True
            print(f"{fmt(new_tvl)} {'✓' if changed else '≈'}")
            updated += 1
        else:
            print("N/D")

    ts = datetime.now(AR_TZ).strftime("%Y-%m-%dT%H:%M:%S%z")
    data["meta"]["updated_at"] = ts
    data["meta"]["source"] = (
        f"Research + DeFiLlama live TVL ({ts[:-9]} ART). "
        "APY estimates: Coin Bureau, Messari, Spark, Babylon, DeFiLlama (may 2026)."
    )

    with open("data/ranking.json", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("─" * 44)
    print(f"{'✅' if updated else '⚠'} {updated} protocolos actualizados de DeFiLlama")

if __name__ == "__main__":
    main()
