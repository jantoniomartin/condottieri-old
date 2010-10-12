#!/bin/sh

WORKON_HOME=/home/jantoniomartin/local
PROJECT_ROOT=/home/jantoniomartin/condottierigame.net/condottieri

#activate virtual environment
source $WORKON_HOME/bin/activate

cd $PROJECT_ROOT
python manage.py send_mail >> $PROJECT_ROOT/logs/cron_mail.log 2>&1
python manage.py emit_notices

