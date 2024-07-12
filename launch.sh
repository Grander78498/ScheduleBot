!/bin/bash

echo "Запуск rabbitmq и celery"
docker run --rm --name rabbitmq -p 5672:5672 rabbitmq:3.13-management &
celery -A django_queue beat -l info &
celery -A django_queue worker -l info