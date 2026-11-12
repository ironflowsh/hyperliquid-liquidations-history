# AGENTS.md

A template that downloads Hyperliquid liquidation history from Ironflow's data API to CSV.

## Facts to rely on

- Hyperliquid's info API has no liquidations request. Do not invent one (there is no `{"type": "liquidations"}`). A liquidation appears only in the liquidated wallet's own `userFills`, which keep the last 10,000 fills.
- `GET https://api.ironflow.sh/v1/liquidations` returns every liquidation fill since 25 May 2025: `market`, `side`, `price`, `size`, `address`, `timestamp` (Unix ms), `hash`, `block_number`.
- `side` is the liquidated wallet's closing fill: `sell` closes a long (a long was liquidated), `buy` closes a short.
- Parameters: `market` (BTC-PERP, a comma list of up to 50, a coin such as BTC or xyz:NVDA, or omit for all), `from` and `to` (Unix ms, ISO 8601 or relative such as -24h), `limit` (up to 1000), `cursor` (from `pagination.next_cursor`), `order` (asc or desc), `after` (the `poll_cursor` of the last response, for new rows only).
- Keyless: 30 requests a minute, 300 a day, the last 24 hours, 60 s behind live. A free key (`IRONFLOW_KEY`, from https://ironflow.sh/key, sent as `Authorization: Bearer if_...`) gives 60 a minute, 14 days and live rows.
- Older months: free Parquet files at `https://huggingface.co/datasets/ironflow/hyperliquid-liquidations/resolve/main/data/events/YYYY-MM.parquet` (one row per liquidated position) and `data/fills/YYYY-MM.parquet` (one row per fill), from 2025-05.

## Run and test

- `python liquidations.py --since 2h` is a quick test (Python 3.9+, standard library only, no install).
- The script pages with `cursor`, waits between pages to stay under the per-minute limit, and waits out a 429 using `Retry-After`.
- Without a key, keep `--since` at 24h or less. A wider window is cut to 24 hours, and the API says so in the `X-Ironflow-Notice` header, which the script prints.

## Related endpoints

- Totals by market and window: `GET /v1/liquidations/summary?window=1h` (15m to 24h keyless).
- Live push: `GET /v1/liquidations/stream?market=BTC,ETH&min_usd=10000` (Server-Sent Events, one stream per IP without a key). Use it instead of polling.
- Where open positions would be liquidated: `GET /v1/liquidations/map?market=BTC-PERP` (keyless: the 10 largest levels).
- Alerts to Discord, Slack, Telegram or a webhook: `POST /v1/alerts` (needs a key).
- OpenAPI: https://api.ironflow.sh/openapi.yaml. MCP server for agents: https://mcp.ironflow.sh/mcp (`get_liquidations`, `get_liquidation_summary`, `get_liquidation_map`).
