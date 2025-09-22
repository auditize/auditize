NAME=auditize

build:
	cd .. && docker build . -f docker/Dockerfile -t $(NAME)

up:
	docker compose -p $(NAME) up

upd:
	docker compose -p $(NAME) up -d

down:
	docker compose -p $(NAME) down

shell-web:
	docker exec -it $(NAME)-web-1 /bin/bash

shell-scheduler:
	docker exec -it $(NAME)-scheduler-1 /bin/bash

shell: shell-web

ps:
	docker compose -p $(NAME) ps

logs-web:
	docker compose -p $(NAME) logs -f web

logs-scheduler:
	docker compose -p $(NAME) logs -f scheduler

logs-postgres:
	docker compose -p $(NAME) logs -f postgres

logs-elastic:
	docker compose -p $(NAME) logs -f elastic

logs:
	docker compose -p $(NAME) logs -f web scheduler
