DIR = $(shell pwd)
ENV_DIR = $(DIR)/.venv/bin
PYTHON_EXEC = $(ENV_DIR)/python3

debug:
	$(PYTHON_EXEC) manage.py runbot --settings=django_queue.settings

celery:
	$(ENV_DIR)/celery -A django_queue beat -l info &
	$(ENV_DIR)/celery -A django_queue worker -l info &

prod: celery
	$(PYTHON_EXEC) manage.py runbot --settings=django_queue.prod_settings