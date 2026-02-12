# ha-intelligence-hub

Adaptive intelligence platform for Home Assistant — real-time activity monitoring, predictive analytics, and an interactive Preact dashboard.

## Context

**Parent project:** `ha-intelligence` at `~/Documents/projects/ha-intelligence/`
**Design doc:** `~/Documents/docs/plans/2026-02-11-ha-intelligence-hub-design.md`
**Lean roadmap:** `~/Documents/docs/plans/2026-02-11-ha-hub-lean-roadmap.md`
**Activity monitor plan:** `~/.claude/plans/resilient-stargazing-catmull.md`

## Running

**Service:** `ha-intelligence-hub.service` (user systemd, enabled, Restart=always)
**API:** `http://127.0.0.1:8001` (localhost only)
**Dashboard:** `http://127.0.0.1:8001/ui/`
**WebSocket:** `ws://127.0.0.1:8001/ws` (real-time cache updates to dashboard)
**Env vars:** HA_URL, HA_TOKEN from `~/.env` (bash wrapper pattern, not EnvironmentFile=)

```bash
# Restart
systemctl --user restart ha-intelligence-hub

# Logs
journalctl --user -u ha-intelligence-hub -f

# Cache inspection
curl -s http://127.0.0.1:8001/api/cache | python3 -m json.tool
curl -s http://127.0.0.1:8001/api/cache/activity_summary | /usr/bin/python3 -m json.tool
```

## Architecture

### Modules (6, registered in order)

| Module | File | Purpose |
|--------|------|---------|
| `discovery` | `modules/discovery.py` | Scans HA (REST + WebSocket), detects capabilities, caches entities/devices/areas |
| `ml_engine` | `modules/ml_engine.py` | Feature engineering, model training (GradientBoosting, RandomForest), periodic retraining |
| `pattern_recognition` | `modules/patterns.py` | Detects recurring event sequences from logbook data |
| `orchestrator` | `modules/orchestrator.py` | Generates automation suggestions from detected patterns |
| `intelligence` | `modules/intelligence.py` | Assembles daily/intraday snapshots, baselines, predictions, ML scores into unified cache. Reads Phase 2-4 engine outputs (entity correlations, sequence anomalies, power profiles, automation suggestions). Sends Telegram digest on new insights. |
| `activity_monitor` | `modules/activity_monitor.py` | WebSocket listener for state_changed events, 15-min windowed activity log, adaptive snapshot triggering, prediction analytics |

### Hub Core

| File | Purpose |
|------|---------|
| `hub/core.py` | `IntelligenceHub` class — module registry, task scheduler, event bus |
| `hub/cache.py` | SQLite-backed cache (hub.db) with category-based get/set |
| `hub/constants.py` | Shared cache key constants (prevents implicit coupling between modules) |
| `hub/api.py` | FastAPI routes + WebSocket server for real-time dashboard updates |
| `bin/ha-hub.py` | Entry point — initializes hub, registers modules, starts uvicorn |
| `bin/discover.py` | Standalone discovery CLI (also used as subprocess by hub) |

### Cache Categories (8)

`activity_log`, `activity_summary`, `areas`, `capabilities`, `devices`, `discovery_metadata`, `entities`, `intelligence`

### Dashboard (Preact SPA)

**Stack:** Preact + Tailwind CSS, bundled with esbuild
**Pages:** Home, Discovery, Capabilities, Intelligence, Patterns, Predictions, Automations

```bash
# Rebuild SPA after JSX changes
cd dashboard/spa && npx esbuild src/index.jsx --bundle --outfile=dist/bundle.js \
  --jsx-factory=h --jsx-fragment=Fragment --inject:src/preact-shim.js \
  --loader:.jsx=jsx --minify
```

**Intelligence page components** (split into `pages/intelligence/`):

| Component | What it shows |
|-----------|---------------|
| `LearningProgress` | Data maturity bar (collecting → baselines → ML training → ML active) |
| `HomeRightNow` | Current intraday metrics vs baselines with color-coded deltas |
| `ActivitySection` | Activity monitor: occupancy, event rates, timeline, patterns, anomalies, WS health |
| `TrendsOverTime` | 30-day metric trends with sparkline charts |
| `PredictionsVsActuals` | Predicted vs actual metric comparison |
| `Baselines` | Hourly baselines per metric with confidence ranges |
| `DailyInsight` | LLM-generated daily insight text |
| `Correlations` | Cross-metric correlation matrix |
| `SystemStatus` | Run log, ML model scores (R2/MAE), meta-learning applied suggestions |
| `Configuration` | Current intelligence engine config |
| `utils.jsx` | Shared helpers: Section, Callout, durationSince, describeEvent, EVENT_ICONS, DOMAIN_LABELS |

### Activity Monitor — Prediction Analytics

Four analytical methods computed on each 15-min flush and cached in `activity_summary`:

| Method | What it does | Cold-start requirement |
|--------|-------------|----------------------|
| `_event_sequence_prediction` | Frequency-based next-domain model from 5-domain n-grams | 6+ events in window history |
| `_detect_activity_patterns` | Frequent 3-domain trigrams (3+ occurrences in 24h) | 3+ recurring sequences |
| `_predict_next_arrival` | Day-of-week historical occupancy transition averages | Occupancy transitions in history |
| `_detect_activity_anomalies` | Current event rate vs hourly historical average (flags >2x) | Hourly average data |

## Testing

```bash
# Run all tests (81 tests, ~0.3s)
.venv/bin/python -m pytest tests/ -v

# Individual test files
.venv/bin/python -m pytest tests/test_activity_monitor.py -v  # 37 tests
.venv/bin/python -m pytest tests/test_intelligence.py -v       # 44 tests
.venv/bin/python -m pytest tests/test_discover.py -v
.venv/bin/python -m pytest tests/test_patterns.py -v
.venv/bin/python -m pytest tests/test_ml_training.py -v
.venv/bin/python -m pytest tests/test_integration.py -v
```

## Environment

- **HA instance:** 192.168.1.35:8123 (HAOS on Raspberry Pi, 3,058 entities, 10 capabilities)
- **Env vars:** HA_URL, HA_TOKEN from `~/.env`
- **Python:** 3.12 via `.venv/` (aiohttp, scikit-learn, numpy, uvicorn, fastapi)
- **Node:** esbuild for SPA bundling (dev dependency only)
- **Cache DB:** `~/ha-logs/intelligence/cache/hub.db` (SQLite)
- **Snapshot log:** `~/ha-logs/intelligence/snapshot_log.jsonl` (append-only JSONL)

## WebSocket Connections

The hub maintains **two separate WebSocket connections** to HA:

1. **Discovery** (`modules/discovery.py`) — listens for `entity_registry/list`, `device_registry/list`, `area_registry/list` (low-frequency registry events)
2. **Activity** (`modules/activity_monitor.py`) — listens for `state_changed` (high-volume, ~22K events/day)

Separated by design: state_changed volume would drown registry events. Each has independent backoff (5s→60s max).

## Domain Filtering (Activity Monitor)

**Tracked:** light, switch, binary_sensor, lock, media_player, cover, climate, vacuum, person, device_tracker, fan
**Conditional:** sensor (only if device_class == "power")
**Excluded:** update, tts, stt, scene, button, number, select, input_*, counter, script, zone, sun, weather, conversation, event, automation, camera, image, remote

**Noise suppression:** unavailable↔unknown transitions, same-state-to-same-state

## Gotchas

- HA WebSocket requires `auth` message with token before subscribing
- Use `/usr/bin/python3` (3.12) not `python3` (3.14, no packages) for manual JSON piping
- SQLite cache persists across restarts — stale data shows until first flush cycle (15 min)
- `activity_summary.websocket` shows `null` until first summary flush after restart (expected)
- Prediction fields start empty on cold boot — need 24-48h of data to populate
- `dist/bundle.js` is gitignored — must rebuild SPA after JSX changes before restart
- `snapshot_log.jsonl` is append-only, never pruned — grows ~1KB/snapshot
- Snapshot subprocess (`ha-intelligence --snapshot-intraday`) uses `asyncio.get_running_loop().run_in_executor` — don't call from sync context
- Module registration order matters — discovery must run before ml_engine (needs capabilities cache)
- Intelligence module reads engine JSON files (entity_correlations, sequence_anomalies, power_profiles, automation_suggestions) — returns `None` gracefully if files don't exist yet
- Engine JSON schema changes require corresponding updates to `_read_intelligence_data()` in `modules/intelligence.py`
