#!/bin/bash

NAME="guess_movie"  # Name of the application
DJANGODIR=/home/tanguy/movizz/guess_movie  # Django project directory
DJANGOENVDIR=/home/tanguy/movizz/venv  # Django project env

echo "Starting $NAME as `whoami`"

# Activate the virtual environment
cd $DJANGODIR
source /home/tanguy/movizz/venv/bin/activate
# source /home/ubuntu/webapp/myproject/proj/.env
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Start daphne
exec ${DJANGOENVDIR}/bin/daphne -u /home/tanguy/movizz/venv/run/daphne.sock --access-log - --proxy-headers guess_movie.asgi:application
