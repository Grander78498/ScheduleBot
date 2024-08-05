DIR = $(shell pwd)
ENV_DIR = $(DIR)/.venv/bin
PYTHON_EXEC = $(ENV_DIR)/python3

debug:
	$(PYTHON_EXEC) manage.py runbot --settings=django_queue.settings

celery:
	sudo systemctl start redis
	$(ENV_DIR)/celery -A django_queue beat -l info -f $(DIR)/logs/beat.log &
	$(ENV_DIR)/celery -A django_queue worker -l info -f $(DIR)/logs/worker.log &

prod: celery
	$(PYTHON_EXEC) manage.py runbot --settings=django_queue.prod_settings