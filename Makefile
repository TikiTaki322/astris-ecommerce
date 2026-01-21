up:
	docker-compose -f docker-compose.dev.yml up -d
down:
	docker-compose -f docker-compose.dev.yml down
build:
	docker-compose -f docker-compose.dev.yml build
rebuild:
	docker-compose -f docker-compose.dev.yml up -d --build
rebuild-backend:
	docker-compose -f docker-compose.dev.yml build backend
	docker-compose -f docker-compose.dev.yml up -d
restart:
	docker-compose -f docker-compose.dev.yml down
	docker-compose -f docker-compose.dev.yml up -d
locust:
	docker exec -it petit_django-backend-1 locust --host=http://localhost:8000
ps:
	docker-compose -f docker-compose.dev.yml ps -a