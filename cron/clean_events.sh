#!/bin/sh

WORKON_HOME=/var/lib
PROJECT_ROOT=/var/www/labs.no-ip.biz/projects/condottieri

#activate virtual environment
. $WORKON_HOME/pinax-env/bin/activate

cd $PROJECT_ROOT
python manage.py clean_events

