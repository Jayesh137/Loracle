# Loracle — Hyperliquid Trader Intelligence

Continuously logs a specific Hyperliquid trader's activity, builds a behavioral
fingerprint from it, and watches for the trader appearing on a new wallet (via
on-chain fund tracing and leaderboard fingerprint matching). Free-infra only:
GitHub Actions for compute, JSON-in-git for storage, GitHub Pages for the dashboard.

See [PRD.md](PRD.md) for product spec and [docs/architecture.md](docs/architecture.md)
for the technical design (including a "what is actually built" status table).

## What's built

- **Collection** (`collector.py`, `backfill.py`) — polls Hyperliquid endpoints on a cron.
- **Fingerprint** (`fingerprint.py`) — reconstructs positions from fills, then computes
  behavioral dimensions (asset mix, timing, leverage, hold duration, position sizing, etc.).
- **Scanner** (`scanner.py`) — scores leaderboard wallets against the fingerprint over a
  symmetric lookback window; weights are in `config.json → scanner.weights`.
- **Tracer** (`tracer.py`) — Arbitrum L1 fund-flow tracing, `known_alts`-aware. Scheduled
  runs are **disabled** (no L1 volume yet); run manually via workflow dispatch.
- **Dashboard** — SvelteKit static site (Home / Fills / Fingerprint / Scanner) reading
  committed JSON via `raw.githubusercontent.com`.

**Not built / dormant:** daily reports (use the dashboard directly); Twitter
monitor + correlator (nitter RSS sources are down).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/backfill.py      # one-time historical pull
python src/collector.py     # ongoing collection
python src/fingerprint.py   # rebuild fingerprint
pytest -q                   # tests
```

### GitHub secrets (for alerts / tracing)

`BREVO_SMTP_KEY`, `ALERT_EMAIL`, `ETHERSCAN_API_KEY`.

## Live pipeline & staleness

Collection runs via scheduled GitHub Actions (`collect.yml`, `scan.yml`, `analyze.yml`).

> **GitHub disables scheduled workflows after a period of repository inactivity, and
> throttles high-frequency (`*/5`) crons.** If the dashboard shows a red "Data is stale"
> banner, go to the repo's **Actions** tab and re-enable / re-run the workflows.

Staleness is detected two ways, both free:
- `collector.py` prints a GitHub `::error::` annotation if the newest fill is > 24h old.
- The dashboard home shows a stale-data banner when `data/index.json`'s freshness is > 6h old.

## Config

`config.json` holds the target wallet, `known_alts`, alert thresholds, and scanner
settings (`fills_lookback_days`, `weights`). Adding an alt to `known_alts[]` requires no
code changes.
