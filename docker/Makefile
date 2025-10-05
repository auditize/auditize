NAME=auditize

build:
	cd .. && docker build . -f docker/Dockerfile -t $(NAME)

up:
	docker compose up

upd:
	docker compose up -d

down:
	docker compose down

shell-web:
	docker exec -it $(NAME)-web-1 /bin/bash

shell-scheduler:
	docker exec -it $(NAME)-scheduler-1 /bin/bash

shell: shell-web

ps:
	docker compose ps

logs-web:
	docker compose logs -f web

logs-scheduler:
	docker compose logs -f scheduler

logs-postgres:
	docker compose logs -f postgres

logs-elastic:
	docker compose logs -f elastic

logs:
	docker compose logs -f web scheduler
