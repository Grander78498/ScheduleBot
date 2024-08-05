#!/bin/bash

dir=$(pwd)
PATH=$PATH:$dir/.venv/bin
celery -A django_queue beat -l info &
celery -A django_queue worker -l info