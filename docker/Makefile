NAME=auditize

build-base:
	cd .. && docker build . -f docker/Dockerfile.base -t $(NAME)/base

build-web:
	cd .. && docker build . -f docker/Dockerfile.web -t $(NAME)/web

build-tasks:
	cd .. && docker build . -f docker/Dockerfile.cron -t $(NAME)/tasks

build: build-base build-web build-tasks

up:
	docker compose -p $(NAME) up -d

down:
	docker compose -p $(NAME) down

shell-web:
	docker exec -it $(NAME)-web-1 /bin/bash

shell-tasks:
	docker exec -it $(NAME)-tasks-1 /bin/bash

shell: shell-web

ps:
	docker compose -p $(NAME) ps

log-web:
	docker compose -p $(NAME) logs -f web

log-tasks:
	docker compose -p $(NAME) logs -f tasks

log:
	docker compose -p $(NAME) logs -f web tasks
