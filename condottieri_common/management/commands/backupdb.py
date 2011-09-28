"""
 Command for backup database
 This snippet was made by msaelices and published in http://djangosnippets.org/snippets/823/
 Redistributed here by the terms in http://djangosnippets.org/about/tos/
 Edited to work with Django-1.2
"""

import os, popen2, time
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Backup database. Only Mysql and Postgresql engines are implemented"

    def handle(self, *args, **options):
        from django.db import connection
        from django.conf import settings

        _conf = settings.DATABASES["default"]

        self.engine = _conf["ENGINE"]
        self.db = _conf["NAME"]
        self.user = _conf["USER"]
        self.passwd = _conf["PASSWORD"]
        self.host = _conf["HOST"]
        self.port = _conf["PORT"]

        backup_dir = os.path.join(os.path.abspath(os.getcwd()), "..", "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, 0700)
        outfile = os.path.join(backup_dir, 'backup_%s.sql' % time.strftime('%y%m%d%S'))

        if self.engine == 'django.db.backends.mysql':
            print 'Doing Mysql backup to database %s into %s' % (self.db, outfile)
            self.do_mysql_backup(outfile)
        elif self.engine == 'django.db.backends.postgresql_psycopg2':
            print 'Doing Postgresql backup to database %s into %s' % (self.db, outfile)
            self.do_postgresql_backup(outfile)
        else:
            print 'Backup in %s engine not implemented' % self.engine

    def do_mysql_backup(self, outfile):
        args = []
        if self.user:
            args += ["--user=%s" % self.user]
        if self.passwd:
            args += ["--password=%s" % self.passwd]
        if self.host:
            args += ["--host=%s" % self.host]
        if self.port:
            args += ["--port=%s" % self.port]
        args += [self.db]

        os.system('mysqldump %s > %s' % (' '.join(args), outfile))

    def do_postgresql_backup(self, outfile):
        args = []
        if self.user:
            args += ["--username=%s" % self.user]
        if self.passwd:
            args += ["--password"]
        if self.host:
            args += ["--host=%s" % self.host]
        if self.port:
            args += ["--port=%s" % self.port]
        if self.db:
            args += [self.db]
        pipe = popen2.Popen4('pg_dump %s > %s' % (' '.join(args), outfile))
        if self.passwd:
            pipe.tochild.write('%s\n' % self.passwd)
            pipe.tochild.close()
