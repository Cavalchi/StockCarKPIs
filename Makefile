.PHONY: setup etl dashboard test lint all

setup:
	pip install -r requirements.txt
	docker-compose up -d

etl:
	python -m stockcar_kpis.etl.load_db

dashboard:
	streamlit run stockcar_kpis/dashboard/streamlit_app.py

plots:
	python -m stockcar_kpis.dashboard.app

test:
	pytest tests/

lint:
	flake8 stockcar_kpis/

all: setup etl dashboard
