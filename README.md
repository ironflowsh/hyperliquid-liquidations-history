# Hyperliquid liquidations history

Download Hyperliquid liquidations for one market, several or all of them, to CSV with totals.

Hyperliquid's info API has no liquidations request. A liquidation only shows up inside the liquidated wallet's own fills, and the API keeps the last 10,000 of those. Ironflow records every liquidation fill from its own Hyperliquid nodes since 25 May 2025.

## Run

```bash
python liquidations.py
```

Python 3.9 or newer, standard library only. No key needed. The default is BTC-PERP over the last 24 hours:

```text
8,070 liquidation fills written to liquidations.csv
longs liquidated $116,643,894, shorts $984,712
  BTC-PERP           8,070 fills  longs $   116,643,894  shorts $       984,712
largest fill: $8,001,220 long on BTC-PERP at 72124, 2026-11-12 13:10 UTC
```

```bash
python liquidations.py --market ETH-PERP,SOL-PERP --since 6h
python liquidations.py --market all --since 2h
python liquidations.py --market xyz:NVDA --out nvda.csv
```

Each row is one liquidation fill: time, market, price, size, notional, the liquidated wallet, and `liquidated` (`long` or `short`). A large liquidation fills in several rows.

## How far back

| Access | History |
|---|---|
| No key | Last 24 hours, 60 s behind live |
| Free key from [ironflow.sh/key](https://ironflow.sh/key) | 14 days, live |
| Plans | 90 days and more: [limits by plan](https://docs.ironflow.sh/concepts/rate-limits) |
| Free monthly files | Every month since May 2025, on [Hugging Face](https://huggingface.co/datasets/ironflow/hyperliquid-liquidations) |

With a key: `IRONFLOW_KEY=if_your_key python liquidations.py --since 14d`.

Older months in pandas (`pip install pandas pyarrow`):

```python
import pandas as pd

url = "https://huggingface.co/datasets/ironflow/hyperliquid-liquidations/resolve/main/data/events/2025-10.parquet"
df = pd.read_parquet(url)
print(df[df.market == "BTC-PERP"].nlargest(5, "notional_usd"))
```

## Live data

- **Stream:** `curl -N "https://api.ironflow.sh/v1/liquidations/stream?market=BTC,ETH&min_usd=10000"` pushes each liquidation as it lands. One stream per IP without a key.
- **Totals:** `GET https://api.ironflow.sh/v1/liquidations/summary?window=24h`
- **Liquidation map:** `GET https://api.ironflow.sh/v1/liquidations/map?market=BTC-PERP` shows where open positions would be liquidated if the price moved.
- **Alerts:** `POST https://api.ironflow.sh/v1/alerts` with a key posts liquidations to Discord, Slack, Telegram or a webhook. [Guide](https://ironflow.sh/guides/hyperliquid-liquidation-data).

## Links

- [Hyperliquid liquidation data guide](https://ironflow.sh/guides/hyperliquid-liquidation-data)
- [API reference](https://docs.ironflow.sh/api-reference/market-data/list-liquidations)
- [Hyperliquid MCP server](https://docs.ironflow.sh/guides/ai-agents) for Claude, Cursor and other agents

## License

MIT. The Hugging Face files carry their own license: see each dataset card.
