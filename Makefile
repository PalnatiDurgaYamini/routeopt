.PHONY: web install fmt lint type test check run docker

install:
	pip install -e ".[dev]"

fmt:
	ruff format .
	ruff check --fix .

lint:
	ruff check .
	ruff format --check .

type:
	mypy

test:
	pytest

check: lint type test

run:
	routeopt generate --n 40 --seed 1 --out orders.csv
	routeopt solve --orders orders.csv --capacity 30 --solver cluster --workers 2

web:
	routeopt serve

docker:
	docker build -t routeopt .
	docker run --rm -v "$(PWD)":/data routeopt generate --n 40 --out orders.csv
	docker run --rm -v "$(PWD)":/data routeopt solve --orders orders.csv --capacity 30
