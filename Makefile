DIR = $(shell pwd)
ENV_DIR = $(DIR)/.venv/bin
PYTHON_EXEC = $(ENV_DIR)/python3

reqs: requirements.txt
	$(ENV_DIR)/pip3 install -r requirements.txt

migrate: reqs queue_api/models.py
	$(PYTHON_EXEC) manage.py makemigrations
	$(PYTHON_EXEC) manage.py migrate

debug: migrate
	$(PYTHON_EXEC) manage.py runbot --settings=django_queue.settings

celery: migrate
	sudo systemctl start redis
	$(ENV_DIR)/celery -A django_queue beat -l info &
	$(ENV_DIR)/celery -A django_queue worker -l info &

prod: celery
	$(PYTHON_EXEC) manage.py runbot --settings=django_queue.prod_settings
