.PHONY: env pipeline api test lint check-models web-citizen web-console

env:
	conda env create -f environment.yml

pipeline:
	python -m pipeline.run all

api:
	uvicorn api.main:app --reload --port 8000

test:
	pytest -q

lint:
	ruff check .

check-models:
	python scripts/check_models.py

web-citizen:
	cd web && npm run dev -w citizen

web-console:
	cd web && npm run dev -w console
