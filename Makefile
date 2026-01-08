.PHONY: up down logs test

up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f api

test:
	# Run tests inside a disposable container to ensure env consistency
	docker build -t app-test .
	docker run --rm -e WEBHOOK_SECRET=testsecret -e DATABASE_URL=:memory: app-test pytest
