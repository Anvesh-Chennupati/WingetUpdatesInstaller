.PHONY: install run test lint clean docker-up docker-down

install:
	uv pip install -e .

run:
	python -m wingetupdatesinstaller.main

test:
	pytest tests/

lint:
	black .
	flake8 .

clean:
	rm -rf build/ dist/ *.egg-info/

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down
