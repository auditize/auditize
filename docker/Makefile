NAME=auditize

build:
	cd .. && docker build . -f docker/Dockerfile -t $(NAME)

up:
	docker compose -p $(NAME) up -d

down:
	docker compose -p $(NAME) down
