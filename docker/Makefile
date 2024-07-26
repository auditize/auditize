NAME=auditize

build:
	cd .. && docker build . -f docker/Dockerfile.base -t $(NAME)/base
	cd .. && docker build . -f docker/Dockerfile.web -t $(NAME)/web

up:
	docker compose -p $(NAME) up -d

down:
	docker compose -p $(NAME) down

shell:
	docker exec -it $(NAME)-web-1 /bin/bash
