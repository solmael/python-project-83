install:
	uv sync --no-install-project

dev:
	uv run flask --debug --app page_analyzer:app run

start:
	PORT ?= 8000
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

render-start:
	PORT ?= 8000
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

lint:
	uv run ruff check .

fix:
	uv run ruff check . --fix

test:
	uv run pytest