#!/usr/bin/env bash
# Day 1. Download raw datasets into data/raw/. Bbox = zone + 5 km buffer (fill from zone.geojson).
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw

# TODO(Day 1): set bbox after drawing data/manual/zone.geojson
WEST=; SOUTH=; EAST=; NORTH=

# Copernicus GLO-30 via OpenTopography (needs a free API key: OPENTOPO_KEY)
# curl -fL "https://portal.opentopography.org/API/globaldem?demtype=COP30&south=$SOUTH&north=$NORTH&west=$WEST&east=$EAST&outputFormat=GTiff&API_Key=$OPENTOPO_KEY" -o data/raw/cop30.tif

# WorldPop India 100 m (constrained or unconstrained; record choice in LICENSES.md)
# curl -fL "<worldpop IND 2020 100m URL>" -o data/raw/ind_pop_100m.tif

# Google Open Buildings: download the S2 tile(s) covering the bbox
# curl -fL "<open buildings tile URL>" -o data/raw/open_buildings.csv.gz
