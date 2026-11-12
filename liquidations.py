"""Download Hyperliquid liquidation history to CSV.

Hyperliquid's info API has no liquidations request: it returns liquidations
only inside one wallet's own fills. Ironflow records every liquidation fill
from its own nodes since 25 May 2025 and serves them at /v1/liquidations.

    python liquidations.py                                # BTC-PERP, last 24 hours
    python liquidations.py --market ETH-PERP,SOL-PERP --since 6h
    python liquidations.py --market all --since 2h
    IRONFLOW_KEY=if_... python liquidations.py --since 14d

Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

API = "https://api.ironflow.sh/v1/liquidations"
KEY = os.environ.get("IRONFLOW_KEY", "")  # optional, from https://ironflow.sh/key
HEADERS = {"User-Agent": os.environ.get("IRONFLOW_USER_AGENT", "hyperliquid-liquidations-history/0.1")}
if KEY:
    HEADERS["Authorization"] = f"Bearer {KEY}"
PAUSE_S = 1.1 if KEY else 2.1  # 60 requests a minute with a key, 30 without
COLUMNS = ["timestamp", "time_utc", "market", "side", "liquidated", "price", "size", "notional_usd",
           "address", "leverage_type", "bankrupt", "block_number", "hash"]


def get(params: dict) -> tuple[dict, str]:
    """One page, and the API's notice if it sent one. Waits out a 429."""
    url = f"{API}?{urllib.parse.urlencode(params)}"
    for _ in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=60) as r:
                return json.load(r), r.headers.get("X-Ironflow-Notice", "")
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            if e.code != 429:
                sys.exit(f"Ironflow API error {e.code}: {body}")
            wait = int(e.headers.get("Retry-After") or 10)
            if wait > 120:
                sys.exit(f"Rate limited for {wait} s: {body}")
            print(f"rate limited, waiting {wait} s", file=sys.stderr)
            time.sleep(wait)
    sys.exit("still rate limited after 5 tries")


def rows(market: str, since: str):
    """Every liquidation fill in the window, oldest first."""
    params = {"from": f"-{since}", "limit": 1000, "order": "asc"}
    if market != "all":
        params["market"] = market
    notices = set()
    while True:
        page, notice = get(params)
        if notice and notice not in notices:
            notices.add(notice)
            print("note:", notice, file=sys.stderr)
        yield from page["data"]
        cursor = page["pagination"].get("next_cursor")
        if not page["pagination"].get("has_more") or not cursor:
            return
        params["cursor"] = cursor
        time.sleep(PAUSE_S)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--market", default="BTC-PERP", help="BTC-PERP, a comma list, a coin (BTC, xyz:NVDA) or all")
    parser.add_argument("--since", default="24h", help="how far back: 30m, 6h, 24h, 14d (24h without a key)")
    parser.add_argument("--out", default="liquidations.csv", help="CSV file to write")
    args = parser.parse_args()

    count, by_market, largest = 0, defaultdict(lambda: [0, 0.0, 0.0]), None
    with open(args.out, "w", newline="") as f:
        out = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        out.writeheader()
        for r in rows(args.market, args.since):
            notional = float(r["price"]) * float(r["size"])
            # side is the liquidated wallet's closing fill: sell closes a long.
            liquidated = "long" if r["side"] == "sell" else "short"
            out.writerow({**r, "notional_usd": round(notional, 2), "liquidated": liquidated,
                          "time_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["timestamp"] / 1000))})
            count += 1
            m = by_market[r["market"]]
            m[0] += 1
            m[1 if liquidated == "long" else 2] += notional
            if largest is None or notional > largest[0]:
                largest = (notional, r["market"], liquidated, r["price"], r["timestamp"])

    print(f"{count:,} liquidation fills written to {args.out}")
    if not count:
        return
    longs = sum(m[1] for m in by_market.values())
    shorts = sum(m[2] for m in by_market.values())
    print(f"longs liquidated ${longs:,.0f}, shorts ${shorts:,.0f}")
    for market, (n, lg, sh) in sorted(by_market.items(), key=lambda kv: -(kv[1][1] + kv[1][2]))[:10]:
        print(f"  {market:<16} {n:>7,} fills  longs ${lg:>14,.0f}  shorts ${sh:>14,.0f}")
    usd, market, side, price, ts = largest
    print(f"largest fill: ${usd:,.0f} {side} on {market} at {price}, "
          f"{time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(ts / 1000))}")


if __name__ == "__main__":
    main()
