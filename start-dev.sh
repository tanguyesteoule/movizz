#!/usr/bin/env bash
sleep 10
cd guess_movie
python manage.py collectstatic --noinput
python manage.py makemigrations
python manage.py migrate
django-admin makemessages --all --ignore=env
django-admin compilemessages --ignore=env
python manage.py runserver 0.0.0.0:80