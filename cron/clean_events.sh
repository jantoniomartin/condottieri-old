#!/bin/sh

WORKON_HOME=/home/jantoniomartin/local
PROJECT_ROOT=/home/jantoniomartin/condottierigame.net/condottieri

#activate virtual environment
source $WORKON_HOME/bin/activate

cd $PROJECT_ROOT
python manage.py clean_events

