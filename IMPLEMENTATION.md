# SafeHaven — Implementation Guide (Day-wise, End to End)

> Source of truth for *what* to build: `implementation&plans/SafeHaven_HLD_LLD.docx` and
> `implementation&plans/SafeHaven_Implementation_Plan.docx`.
> This file is the source of truth for *how and in what order*: exact files, commands,
> checks and commits for each day.

| | |
|---|---|
| Build window | Mon 26 Oct → Wed 4 Nov 2026 (Day 0 → Day 9) |
| Internal deadline | **Wed 4 Nov, 9:00 PM IST** |
| Hard deadline | Thu 5 Nov, 7:30 AM IST (4 Nov, 9:00 PM ET) |
| Zone | Kiratpur + Ghanshyampur blocks, Darbhanga, Bihar (~15 × 15 km), EPSG:32645 |
| Replay | Kosi flood, 27 Sep → 7 Oct 2024 (breach near Kiratpur, 29–30 Sep) |
| Gates | **Gate 1** end of Day 3 (core works) · **Gate 2** end of Day 8 (feature freeze) |

---

## 0. Ground rules

1. **Code decides, models perceive and talk.** Routes, camp sites and rescue priority are computed in `engine/`. Models never pick them.
2. **Every feature has a fallback.** Model down → buttons + template text. Network down → on-device routing.
3. **Heavy work offline, light work live.** `pipeline/` (geopandas, rasterio, pysheds) runs on your laptop and writes `data/processed/`. The API only loads `.npy`, `.json` and `.graphml` files, so the Docker image stays small and needs no GDAL.
4. **Deploy from Day 2.** A live URL must exist before any feature is "done".
5. **One commit + one `BUILDLOG.md` line at the end of each day.** The build log turns into the write-up.
6. **Missed a gate by more than half a day?** Apply the cut list (§12) immediately.

---

## 1. Repository structure (target)

Files marked ★ are created in this scaffold already; everything else is created on the day shown.

```
safehaven/
├── README.md                     ★ pitch, links, judge login, setup (finalised Day 9)
├── IMPLEMENTATION.md             ★ this file
├── DECISIONS.md                  ★ Day 0 decisions (tool calling, Maithili, Glimmer host…)
├── BUILDLOG.md                   ★ two lines per day
├── .gitignore                    ★
├── .env.example                  ★
├── environment.yml               ★ conda env for the offline pipeline (GDAL stack)
├── requirements.txt              ★ slim runtime deps for API image
├── requirements-dev.txt          ★ pytest, ruff
├── pyproject.toml                ★ ruff + pytest config
├── Makefile                      ★ make pipeline / api / test / web …
├── Dockerfile                    Day 2 (hello-world), finalised Day 8
├── render.yaml                   Day 2 (or railway.json)
│
├── implementation&plans/         existing design docs (.docx)
│
├── data/
│   ├── manual/                   ★ COMMITTED small hand-made inputs
│   │   ├── zone.geojson             Day 1  polygon drawn on geojson.io
│   │   ├── breach.geojson           Day 1  breach point + embankment line
│   │   ├── official_sites.csv       Day 1  Darbhanga/BSDMA relief centres
│   │   ├── river_daily.csv          Day 1  WRD bulletins: date, level, warning, danger, birpur_cumecs
│   │   ├── validation.csv           Day 1  15–20 flooded villages: name, lat, lon, source
│   │   └── LICENSES.md              Day 1  source + licence for every dataset/photo
│   ├── raw/                      ★ git-ignored downloads
│   ├── processed/                ★ git-ignored pipeline outputs (bundled into image Day 8)
│   │   ├── walk.graphml, drive.graphml, sites.geojson
│   │   ├── dem.tif, hand.tif, depr.tif, pop.tif, static_S.npy
│   │   ├── rain_hourly.nc, river_hourly.csv
│   │   ├── risk/{hour}.npy        hourly risk grid (uint8 0–255)
│   │   ├── breach/{hour}.npy      breach mask
│   │   ├── edges/{walk,drive}_{hour}.npy   edge risk arrays
│   │   ├── tiles/{hour}/{z}/{x}/{y}.png
│   │   ├── demand/{hour}.json     ~150 m demand clusters
│   │   └── snapshots/{hour}.json.gz
│   └── samples/                  Day 5  demo photo gallery + 1 drone clip (licensed)
│
├── pipeline/                     OFFLINE (conda env) — writes data/processed/
│   ├── __init__.py               ★
│   ├── zone.py                   ★ Day 1  load zone, CRS helpers 32645↔4326, 30 m grid
│   ├── roads.py                  ★ Day 1  osmnx walk + drive graphs
│   ├── buildings.py              ★ Day 1  Google Open Buildings footprints → villages/candidates
│   ├── sites.py                  ★ Day 1  OSM + official shelters/camp candidates
│   ├── terrain.py                ★ Day 1  DEM, HAND (pysheds), depression depth
│   ├── population.py             ★ Day 1  WorldPop 100 m → 30 m (sum-preserving)
│   ├── rainfall.py               ★ Day 1  Open-Meteo hourly rain + discharge, IDW
│   ├── river.py                  ★ Day 1  river_daily.csv → hourly levels
│   ├── precompute.py             ★ Day 2  hourly risk, edge risks, tiles, demand
│   ├── snapshot.py               ★ Day 8  gzip JSON offline bundles + deltas
│   └── run.py                    ★ CLI: python -m pipeline.run [step|all]
│
├── engine/                       PURE LOGIC — numpy/networkx only, unit-tested
│   ├── __init__.py               ★
│   ├── config.py                 ★ ALL weights + thresholds (exported into snapshot)
│   ├── grid.py                   ★ Day 2  load rasters as arrays, lat/lon ↔ cell
│   ├── risk.py                   ★ Day 2  S, R24, report effect C, combine
│   ├── breach.py                 ★ Day 2  hourly breach spread (priority queue)
│   ├── routing.py                ★ Day 3  edge cost, KD-tree snap, multi-target Dijkstra, top-k
│   ├── siting.py                 ★ Day 3  demand, candidates, coverage, greedy MCLP, capacity
│   ├── priority.py               ★ Day 3  rescue priority score
│   ├── depth.py                  ★ Day 5  masks → submerged fraction → ankle/knee/waist/above
│   └── vision.py                 ★ Day 5  SAM 3.1 client, photo/video/aerial analysis
│
├── api/                          FastAPI runtime
│   ├── __init__.py               ★
│   ├── main.py                   ★ Day 2  app, CORS, routers, startup loads data
│   ├── settings.py               ★ Day 2  env vars (pydantic-settings)
│   ├── state.py                  ★ Day 3  in-memory graphs, risk grids, KD-trees
│   ├── db.py                     ★ Day 3  SQLite WAL + SQLAlchemy tables
│   ├── models.py                 ★ Day 3  Pydantic request/response schemas
│   ├── auth.py                   ★ Day 7  JWT + roles, seeded accounts
│   ├── events.py                 ★ Day 7  SSE broadcaster
│   ├── seed.py                   ★ Day 3  seed sites + demo/judge users
│   └── routers/
│       ├── __init__.py           ★
│       ├── health.py             ★ Day 2  GET /health
│       ├── route.py              ★ Day 3  GET /route
│       ├── sites.py              ★ Day 3  GET /sites, PATCH /console/sites/{id}
│       ├── tiles.py              ★ Day 3  GET /risk-tiles/{hour}/{z}/{x}/{y}.png
│       ├── reports.py            ★ Day 3/5  POST /reports, GET /console/reports
│       ├── rescue.py             ★ Day 3/7  POST /rescue, GET/PATCH /console/rescue
│       ├── planning.py           ★ Day 3  POST /console/plan
│       ├── video.py              ★ Day 5  POST /console/video (background job)
│       ├── assistant.py          ★ Day 6  POST /assistant, POST /console/copilot
│       ├── sms.py                ★ Day 6  POST /sms/inbound
│       ├── alerts.py             ★ Day 7  POST /console/alerts, /approve
│       ├── snapshot.py           ★ Day 8  GET /snapshot/latest, delta
│       └── events.py             ★ Day 7  GET /events (SSE)
│
├── llm/
│   ├── __init__.py               ★
│   ├── client.py                 ★ Day 0/6  OpenAI-SDK-compatible Meta Model API client
│   ├── tools.py                  ★ Day 6  tool registry (citizen + copilot), JSON schemas
│   ├── agent.py                  ★ Day 6  agent loop: ≤4 tool calls, 15 s, retry, fallback
│   ├── validators.py             ★ Day 6  Pydantic output checks + place-name check
│   ├── edge_glimmer.py           ★ Day 8  local Glimmer adapter (edge mode)
│   └── prompts/
│       ├── citizen.md            ★ Day 6
│       ├── copilot.md            ★ Day 6
│       ├── report.md             ★ Day 6
│       └── explain.md            ★ Day 6
│
├── scripts/
│   ├── check_models.py           ★ Day 0  one call each: Muse Spark (hi/mai/tools), SAM 3.1
│   ├── fetch_data.sh             ★ Day 1  DEM / WorldPop / Open Buildings downloads
│   ├── eval_routes.py            ★ Day 3/9  50-origin safety + latency
│   ├── eval_risk.py              ★ Day 2  validation villages vs peak risk
│   ├── eval_sam.py               ★ Day 5  30 photos depth accuracy, 20 aerial P/R
│   ├── eval_agent.py             ★ Day 6  20 inputs × 3 languages
│   └── export_parity.py          ★ Day 8  50 origins + server routes → web test fixture
│
├── web/                          npm workspaces (Node 20+)
│   ├── package.json              Day 4
│   ├── shared/src/
│   │   ├── api.ts                Day 4  fetch with 3 s timeout, cloud→edge→offline
│   │   ├── map/                  Day 4  BaseMap, RiskLayer, RouteLayer, SitesLayer
│   │   ├── i18n/{hi,mai,en}.json Day 4
│   │   ├── replay/TimeSlider.tsx Day 4
│   │   └── offline/              Day 8  snapshot.ts, router.ts (ngraph.path), queue.ts (idb)
│   ├── citizen/                  Day 4  Vite React PWA
│   │   └── src/{App.tsx, screens/{Home,Result,Rescue,Report,Chat}.tsx, sw.ts}
│   └── console/                  Day 7  Vite React dashboard
│       └── src/{App.tsx, Login.tsx, screens/{Situation,Reports,Rescue,Planning,Video,Copilot}.tsx}
│
├── tests/
│   ├── conftest.py               ★ tiny synthetic graph + grid fixtures
│   ├── test_config.py            ★ thresholds sane (runs from Day 0, keeps CI green)
│   ├── test_risk.py              ★ Day 2
│   ├── test_breach.py            ★ Day 2
│   ├── test_routing.py           ★ Day 3  route safety: no edge above threshold
│   ├── test_siting.py            ★ Day 3  greedy MCLP sanity
│   ├── test_priority.py          ★ Day 3
│   ├── test_depth.py             ★ Day 5
│   ├── test_validators.py        ★ Day 6
│   └── test_api.py               ★ Day 3  FastAPI TestClient smoke
│
└── .github/workflows/ci.yml      ★ ruff + pytest on every push
```

---

## 2. Critical path (what blocks what)

```
Day0 env+keys ─► Day1 data ─► Day2 risk+breach ─► Day3 routing+siting+API ══ GATE 1
                                                     │
              ┌──────────────────────────────────────┼──────────────────────┐
              ▼                                      ▼                      ▼
        Day4 citizen PWA                     Day5 SAM 3.1            Day6 Muse Spark agents
              └───────────────► Day7 console ◄───────┴──────────────────────┘
                                     ▼
                     Day8 offline + edge + deploy ══ GATE 2 (freeze)
                                     ▼
                         Day9 metrics, video, submit
```

If Day 1 data is late, everything slips. Time-box HAND to 4 h, and keep the fallbacks ready.

---

## 3. Day 0 — Mon 26 Oct · Setup and de-risking

**Goal:** every external dependency answers once. Decisions written down.

### Tasks
- [ ] Repo skeleton (this scaffold) committed and pushed.
- [ ] Conda env for the pipeline:
      `conda env create -f environment.yml && conda activate safehaven`
- [ ] Runtime/dev deps work in the same env: `pip install -r requirements.txt -r requirements-dev.txt`
- [ ] `cp .env.example .env`, fill `META_API_KEY`, `META_API_BASE_URL`, model ids from the Meta Model API docs.
- [ ] `python scripts/check_models.py` runs:
  - Muse Spark: Hindi prompt, Maithili prompt (have a native speaker rate it), one call with a tool definition.
  - SAM 3.1: one flood photo with prompts `water, person, cow, roof`; note the mask format and latency.
- [ ] Decide where Glimmer runs (laptop RAM/GPU, or Modal/Baseten).
- [ ] Optional: WhatsApp Cloud API test number. Hard stop at 2 h.
- [ ] Start a footage folder: Kosi 2024 photos and drone clips with clear reuse rights. Log each in `data/manual/LICENSES.md`.
- [ ] Kickoff livestream (10:30 PM IST); read the Official Rules; list the submission fields in `DECISIONS.md`.

### Done when
`check_models.py` prints OK for all three checks, and `DECISIONS.md` has all four answers filled in.

### Fallbacks
No tool calling → JSON mode, with the backend executing tools (same tool schemas). Weak Maithili → Hindi carries the demo, and Maithili goes on the cut list.

**Commit:** `chore: project scaffold, env and model checks`

---

## 4. Day 1 — Tue 27 Oct · Data foundation

**Goal:** every layer for the zone, aligned in EPSG:32645, checked in QGIS.

### Files
`pipeline/zone.py, roads.py, buildings.py, sites.py, terrain.py, population.py, rainfall.py, river.py, run.py`, `scripts/fetch_data.sh`, all of `data/manual/*`

### Tasks (in this order, so slow downloads run while you work)
1. [ ] **Zone** (30 min): draw the polygon on geojson.io → `data/manual/zone.geojson`. `zone.py`: `load_zone()`, `to_utm()`, `to_wgs()`, `grid_spec()` (30 m grid, origin and shape shared by every raster).
2. [ ] **Kick off downloads** (`scripts/fetch_data.sh`): Copernicus GLO-30 with a 5 km buffer (OpenTopography), WorldPop IND 100 m, Google Open Buildings tiles for the bbox.
3. [ ] **Roads** (`roads.py`): `ox.graph_from_polygon(zone, network_type="walk"|"drive")`, simplified, project to 32645, keep `highway, length, steps`. Check coverage in QGIS, since rural Bihar is thinly mapped. Note any missing tracks.
4. [ ] **Terrain** (`terrain.py`, **4 h time-box**): reproject DEM → `dem.tif`; pysheds fill pits → fill depressions → resolve flats → D8 → accumulation → stream threshold tuned to the Kosi channels → `compute_hand` → `hand.tif`; `depr.tif = filled − dem`.
5. [ ] **Population** (`population.py`): clip WorldPop and resample to the 30 m grid, preserving the sum (divide by 11.1, or use `rasterio.warp.reproject` with `Resampling.sum`). Assert totals match within 1%.
6. [ ] **Buildings + sites** (`buildings.py`, `sites.py`): OSM schools, colleges, community centres, PHCs/hospitals, places of worship, public buildings, `man_made=dyke` embankment tops; add Open Buildings footprints (area ≥ 500 m²) as "possible" candidates; merge `official_sites.csv` with `official=true` → `sites.geojson`.
7. [ ] **Rain + river** (`rainfall.py`, `river.py`): Open-Meteo archive, hourly precipitation, 3×3 points, 27 Sep–7 Oct 2024, IDW per hour → `rain_hourly.nc`. Open-Meteo flood API discharge as backup. Transcribe the WRD bulletins → `river_daily.csv` → interpolate to `river_hourly.csv`.
8. [ ] **Breach + validation**: `breach.geojson` (point + time window + embankment line) from news reports; `validation.csv` with 15–20 villages and their sources.

### Done when
`python -m pipeline.run all` rebuilds everything. In QGIS, low HAND follows the Kosi channels and the validation villages sit in low areas.

### Fallbacks
HAND fails → susceptibility = normalised (elevation percentile + distance to river). WRD bulletins unreadable → Open-Meteo discharge only.

**Commit:** `feat(pipeline): zone, roads, terrain, population, sites, rain/river layers`

---

## 5. Day 2 — Wed 28 Oct · Risk engine, breach simulation, first deploy

**Goal:** an hour-by-hour flood picture that matches what happened, plus a live hello-world API.

### Files
`engine/config.py, grid.py, risk.py, breach.py`, `pipeline/precompute.py`, `scripts/eval_risk.py`, `tests/test_risk.py, test_breach.py`, `api/main.py, settings.py, routers/health.py`, `Dockerfile`, `render.yaml`

### Tasks
- [ ] `risk.static_susceptibility(hand, depr)`: `S = 0.6·clip(1−HAND/10) + 0.4·clip(depr/1.5)`.
- [ ] `risk.forcing(hour)`: `R_rain = clip(rain_24h/200)`, `R_river = clip((level−warn)/(danger−warn))`, `R24 = max(…)`.
- [ ] `breach.spread(hour, dem, breach, level_fn, head_loss, max_cells, prev_mask)`: priority queue, lowest ground first, capped cells per hour (outline in the Implementation Plan §4). About 5 h of work.
- [ ] `risk.report_effect(reports, grid, hour)`: `C = max level_w·exp(−d/100 m)·exp(−age/6 h)`. Text-only reports get ×0.5.
- [ ] `risk.combine(...)`: `min(1, w1·S·(1+w2·R24) + w3·max(F_obs,F_breach) + w4·C)`.
- [ ] `precompute.py`: for each hour 0…263 (27 Sep 00:00 → 7 Oct 23:00), write `risk/{h}.npy` (uint8), `breach/{h}.npy`, edge risks (max of samples every 20 m) for walk and drive, PNG tiles for z 11–15, demand clusters.
- [ ] `eval_risk.py`: share of validation villages with risk ≥ 0.6 at peak → `docs/validation_report.md`. Tune `head_loss` and `max_cells`.
- [ ] Hello-world FastAPI `/health` → Docker → Render (or Railway). Save the public URL in `README.md`.

### Done when
Stepping through the hours shows water spreading from the breach into villages, most validation villages end up flooded, and the public `/health` returns 200.

### Fallback
Spread model misbehaves → a distance-and-elevation mask that grows from the breach each hour.

**Commit:** `feat(engine): risk fusion, breach spread, hourly precompute; deploy health API`

---

## 6. Day 3 — Thu 29 Oct · Routing + planning core ══ GATE 1

**Goal:** the decision logic answers over HTTP in under a second.

### Files
`engine/routing.py, siting.py, priority.py`, `api/state.py, db.py, models.py, seed.py`, `api/routers/{route,sites,tiles,reports,rescue,planning}.py`, `tests/test_routing.py, test_siting.py, test_priority.py, test_api.py`, `scripts/eval_routes.py`, `.github/workflows/ci.yml`

### Tasks
- [ ] `routing.edge_cost(length, risk, mode)`: `length·(1+10·risk)`. Block above 0.7 (walk), 0.4 (vehicle), 0.5 (offline).
- [ ] KD-tree snap (`scipy.spatial.cKDTree`) on node coords. One Dijkstra from the origin (`nx.single_source_dijkstra` with a cutoff) until all shelters are settled.
- [ ] Shelter score `0.4(1−site_risk)+0.2·levels+0.2·type+0.2·official`. Rank = `cost/(0.5+score)`. Return the top 3 with GeoJSON and `facts`.
- [ ] Needs: `mobility` drops `steps` edges and caps distance at 1.5 km; `medical` boosts PHCs and hospitals.
- [ ] No-route fallback: highest reachable node within 1 km (often the embankment) + "move to higher ground, call 112".
- [ ] `siting.py`: demand (risk ≥ 0.5 now or in the next 12 h, clustered at ~150 m) → candidates (risk < 0.3 for 24 h, drive-reachable, ≥ 2 levels or ≥ 500 m², official always included) → coverage (walk Dijkstra ≤ D) → greedy MCLP with locked sites first → capacity variant for food points.
- [ ] `priority.score = people × severity × vulnerability × wait_factor`.
- [ ] SQLite WAL, all 9 tables (LLD §10.8). `seed.py` loads sites and demo users.
- [ ] Endpoints: `/route`, `/sites`, `/risk-tiles`, `/reports` (text only for now), `/rescue`, `/console/plan`, `/health`. Every response carries `data_hour` and `snapshot_version`.
- [ ] CI: ruff + pytest on push.

### Done when (Gate 1)
- `scripts/eval_routes.py`: 50 random origins at peak hour → **0 edges above threshold**, p95 < 1 s.
- `POST /console/plan {k:3, max_walk_m:2000}` returns ranked sites with people covered.
- CI is green.

### Fallback
Siting slow → fewer clusters or candidates. The capacity variant moves to the cut list.

**Commit:** `feat: flood-aware routing, MCLP camp siting, core API (Gate 1)`

---

## 7. Day 4 — Fri 30 Oct · Citizen PWA

**Goal:** someone on a phone taps a location in the replay and sees a safe route.

### Setup
```bash
cd web && npm init -y            # then set "workspaces": ["shared","citizen","console"]
npm create vite@latest citizen -- --template react-ts
npm i -w citizen react-leaflet leaflet idb workbox-window
npm i -D -w citizen vite-plugin-pwa
```

### Files
`web/shared/src/{api.ts, map/*, i18n/*, replay/TimeSlider.tsx}`, `web/citizen/src/{App.tsx, screens/Home.tsx, Result.tsx, Rescue.tsx, Report.tsx}`

### Tasks
- [ ] `api.ts`: `VITE_API_URL`, 3 s timeout, typed responses.
- [ ] Location: geolocation (HTTPS), then tap-a-pin, then landmark search. Out-of-zone message with 112.
- [ ] Home: full-screen map, big **Find safe spot** / **I need rescue** buttons, network badge, language toggle (Hindi default).
- [ ] Risk tile overlay plus the replay `TimeSlider` (passes `hour` to every call).
- [ ] Result card: name, *official* vs *possible high ground*, distance, walk time, road to avoid, an "Open in Google Maps" deep link.
- [ ] Rescue form: people, needs (elderly, children, medical), optional phone.
- [ ] Report form: photo + note. The depth picker stays hidden until Day 5.
- [ ] 48 px targets, WCAG AA contrast, short text. Deploy to Vercel.

### Done when
On a real phone over mobile data, the Vercel URL shows a route that changes as you move the slider to peak.

**Commit:** `feat(web): citizen PWA — locate, safe spot, route, rescue, report`

---

## 8. Day 5 — Sat 31 Oct · Vision with SAM 3.1

**Goal:** photos and video become flood data that reroutes people and raises rescue alerts.

### Files
`engine/vision.py, depth.py`, `api/routers/reports.py` (photo path), `api/routers/video.py`, `scripts/eval_sam.py`, `tests/test_depth.py`, `data/samples/`

### Tasks
- [ ] `vision.segment(image, prompts)`: resize to 1024 px, strip EXIF except GPS and time, call SAM 3.1, keep masks with confidence > 0.5. Cache results by image hash.
- [ ] `depth.estimate(masks)`: find a reference object touching water, take the waterline, compute the submerged fraction, map it to a level using this merged table:

  | Reference | Height | Ankle | Knee | Waist | Above |
  |---|---|---|---|---|---|
  | Standing person | 1.65 m | <0.10 | 0.10–0.30 | 0.30–0.60 | >0.60 |
  | Cow (shoulder) | ~1.4 m | <0.15 | 0.15–0.35 | 0.35–0.60 | >0.60 |
  | Hand pump | ~1.0 m | <0.25 | 0.25–0.50 | 0.50–0.80 | >0.80 |
  | Door | 2.1 m | <0.07 | 0.07–0.25 | 0.25–0.50 | >0.50 |
  | Car | 1.5 m | <0.15 | 0.15–0.35 | 0.35–0.60 | >0.60 |

  Confidence = mask confidence × agreement between references. No reference found → return `None`, and the UI shows the depth picker (`level_source=user`).
- [ ] Report effect live: on a new report, update `C` around it, re-score affected edges in memory, merge duplicates within 50 m / 30 min (raise confidence instead).
- [ ] Video (`/console/video`, background task): 1 fps, max 60 frames. Road+water: water > 60 % of the road mask for 3 consecutive frames → block matched edges within 30 m (`F_obs=1`).
- [ ] Aerial: a person mask whose bottom sits on a roof mask, with water within 3 m → `rescue_requests(source=sam, status=unconfirmed)` with a crop.
- [ ] Eval: 30 hand-labelled photos (target ≥ 70 % exact, ≥ 95 % within one level) and 20 aerial frames (precision and recall) → numbers into `BUILDLOG.md`.
- [ ] Demo gallery: 6–8 photos + 1 clip in `data/samples/`.

### Done when
Submitting a knee-deep photo next to a route reroutes it, a drone frame adds an unconfirmed rescue candidate, and the eval numbers are recorded.

**Commit:** `feat(vision): SAM 3.1 depth from photos, flooded roads from video, stranded detection`

---

## 9. Day 6 — Sun 1 Nov · Agents and channels (Muse Spark)

**Goal:** citizens and officials talk to SafeHaven in their own words.

### Files
`llm/client.py, tools.py, agent.py, validators.py, prompts/*.md`, `api/routers/assistant.py, sms.py`, `scripts/eval_agent.py`, `tests/test_validators.py`

### Tasks
- [ ] `client.py`: OpenAI SDK with `base_url=META_API_BASE_URL`, 15 s timeout, one retry.
- [ ] `tools.py`: one registry. Citizen: `find_safe_route, geocode_landmark, submit_report, request_rescue, get_shelter_status`. Copilot adds `query_reports, coverage_gaps, recommend_sites, rank_rescue_queue, draft_sitrep, draft_alert`. Each tool is a thin wrapper over `engine/` and `db`.
- [ ] `agent.py`: native tool calling, or JSON mode if Day 0 said no. Max 4 tool calls per turn, 15 s total, fallback returns `{fallback: true, buttons: [...]}`.
- [ ] `validators.py`: Pydantic for every tool arg and answer. Place-name check: every proper noun in the answer must appear in the tool results. Append 112 and the Bihar SDMA helpline.
- [ ] Prompts: citizen (user's language and script, ≤ 3 sentences, always call a tool for locations), copilot (numbers only from tools, recommendations labelled as such, alerts are drafts), report structuring, explain.
- [ ] `/sms/inbound`: plain text in → one ≤ 160-char reply (simulated).
- [ ] `eval_agent.py`: 20 inputs × (hi, mai, en), including typos and Hinglish. Log pass, fallback or fail.
- [ ] Chat drawer in the citizen app (browser speech recognition where available).

### Done when
60/60 inputs pass or fall back cleanly, and one Hindi or Maithili exchange is good enough for the video.

**Commit:** `feat(llm): Muse Spark citizen assistant + authority copilot with guarded tools`

---

## 10. Day 7 — Mon 2 Nov · Authority console

**Goal:** an official plans camps, watches a report arrive live and assigns a rescue.

### Setup
`npm create vite@latest console -- --template react-ts` (inside `web/`), reuse `@safehaven/shared`.

### Files
`api/auth.py, events.py`, `api/routers/{events,alerts}.py`, `api/routers/rescue.py` (PATCH), `api/routers/sites.py` (PATCH), `web/console/src/**`

### Tasks
- [ ] JWT auth with short expiry. Roles: authority, rescue, ngo, camp_manager, admin. Seed a read-only **judge** account.
- [ ] SSE `/events` (reports, rescue, blocked_edges, alerts). The client falls back to polling every 15–30 s.
- [ ] Situation map: risk, breach extent, reports by level, rescue, camps, blocked roads, uncovered clusters, time slider.
- [ ] Report feed: photo, SAM level, confidence, merged duplicates.
- [ ] Rescue queue: priority-sorted, evidence thumbnails, confirm / assign team (boat or vehicle) / close.
- [ ] Planning: kind (camp or food), k, D → sites and coverage on the map, people covered, gaps, lock and recompute.
- [ ] Video upload screen: progress, frames with masks, edges blocked, candidates created.
- [ ] Copilot panel with **Draft sitrep** and **Draft alert** buttons. Alerts need **Approve**.
- [ ] Deploy the console to Vercel. Set CORS to the two frontend origins.

### Done when
Logged in as authority, you run camp siting for k=3, a phone submits a photo and it appears live, and you assign a team to a rescue.

**Commit:** `feat(web): authority console — live map, reports, rescue queue, planning, copilot`

---

## 11. Day 8 — Tue 3 Nov · Offline, edge node, replay, full deploy ══ GATE 2

**Goal:** every demo scene runs on the live URL, including in airplane mode.

### Files
`pipeline/snapshot.py`, `api/routers/snapshot.py`, `llm/edge_glimmer.py`, `scripts/export_parity.py`, `web/shared/src/offline/{snapshot,router,queue}.ts`, `web/citizen/src/sw.ts`, final `Dockerfile`

### Tasks
- [ ] Snapshot: gzip JSON `{version, hour, hash, config, nodes[[id,lat,lon]], edges[[u,v,len,risk_q,flags]], sites}`, 2–4 MB target. Delta endpoint by version.
- [ ] PMTiles for the zone (Protomaps `pmtiles extract`) served as a static asset.
- [ ] Workbox: cache-first for the shell, PMTiles and snapshot; network-first with a 3 s timeout for API calls; stale-while-revalidate for sites.
- [ ] `router.ts` (ngraph.path): same cost function, thresholds read from `snapshot.config`, offline block at 0.5, data-age label.
- [ ] Parity: `export_parity.py` writes 50 origins + server answers → a JS test asserts 50/50 identical.
- [ ] `queue.ts`: IndexedDB `pending_reports`, `pending_rescue`; Background Sync; client UUIDs; server de-duplicates.
- [ ] Edge mode: `EDGE_MODE=1` uses Glimmer through `edge_glimmer.py` with copilot tools disabled. Phones try cloud → edge → device.
- [ ] Demo mode as the default landing page: "Replay of the Kosi flood, Sep–Oct 2024", sample gallery, judge login shown.
- [ ] Full deploy (Implementation Plan §10.1): data bundle into the image, persistent disk, env vars, CORS, keep-alive ping every 10 min, uptime monitor, tag `v1.0-submission`.
- [ ] User tests: 5 people from Bihar, plus 1 NGO or relief volunteer. Collect one quote.
- [ ] Rehearse every scene twice on two phones over mobile data.

### Done when (Gate 2 — feature freeze)
All 8 video scenes (§14 of the HLD/LLD) pass twice in a row on the live URL.

**Commit:** `feat: offline snapshot + on-device routing, Glimmer edge node, demo mode (Gate 2)`

---

## 12. Day 9 — Wed 4 Nov · Prove and ship

**Fixes only. No new features.**

- [ ] Run all metrics → README table:

  | Metric | Target | Script |
  |---|---|---|
  | Route-safety violations at peak | 0 | `eval_routes.py` |
  | Server/device parity | 50/50 | web parity test |
  | Validation villages in modelled flood | report % | `eval_risk.py` |
  | SAM depth accuracy (30 photos) | ≥70 % exact, ≥95 % ±1 | `eval_sam.py` |
  | Stranded detection P/R (20 frames) | report | `eval_sam.py` |
  | Agent robustness | 60/60 pass or fallback | `eval_agent.py` |
  | `/route` p95 | < 1 s | `eval_routes.py` |
- [ ] Record each scene separately, edit to under 3:00, add captions.
- [ ] README: pitch, screenshots, live links, judge login, architecture diagram, Meta model usage, guardrails, data credits and licences, setup, limitations. Note that Muse Code was used as a dev tool, if that applies.
- [ ] Write-up from `BUILDLOG.md`.
- [ ] Submission checklist (Implementation Plan §13.1). Submit on Cerebral Valley **by 9 PM IST**.

**Commit + tag:** `docs: metrics, README, write-up` → `git tag v1.0-submission`

---

## 13. Cut list (drop from the top when a gate slips)

1. Glimmer edge node (keep on-device routing + template text)
2. WhatsApp channel (keep the SMS-style box)
3. Broadcast alerts + camp-manager updates
4. Food-point capacity planner (keep camp siting)
5. Maithili (keep Hindi + English)
6. Video road flooding (keep photo depth + stranded detection from stills)

**Never cut:** citizen routing, breach replay, camp siting, ≥1 SAM 3.1 + ≥1 Muse Spark feature on screen, the airplane-mode scene, the live URL, the video.

---

## 14. Daily rhythm

- **Morning:** re-read today's section and its "Done when". Check Model API spend (budget $150).
- **Midday:** push working code. Redeploy if anything user-facing changed.
- **Evening:** commit, push, two lines in `BUILDLOG.md`, first task for tomorrow.

## 15. Notes on the design docs

- The **reference-object depth table** differs between the docs (the HLD uses a car; the plan uses a cow and a hand pump). §8 above merges both.
- **Breach simulation** (`engine/breach.py`) and **Google Open Buildings** (`pipeline/buildings.py`) appear only in the Implementation Plan, so they were added to the LLD repo layout.
- The LLD's single `api/routers/agent.py` is split into `assistant.py` (citizen + copilot), `sms.py` and `alerts.py`, to keep each router small.
- The pipeline (GDAL stack) and runtime are split into `environment.yml` and `requirements.txt`, so the API image stays slim.
