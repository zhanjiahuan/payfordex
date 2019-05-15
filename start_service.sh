#!/bin/bash
nohup celery -A app.tasks_pay.main worker -l info &
gunicorn  --config=gunicorn.conf wsgi_gunicorn:app --log-level=info