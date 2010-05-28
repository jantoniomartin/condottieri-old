from datetime import datetime, timedelta

from django.core.management.base import NoArgsCommand, CommandError

from notification import models as notification

AGE=10*24*60*60

class Command(NoArgsCommand):
	"""
This script deletes all notices that are older than AGE days.
	"""
	help = 'This command deletes all notices that are older than AGE days.'

	def handle_noargs(self, **options):
		age = timedelta(0, AGE)
		threshold = datetime.now() - age
		print "Deleting notices that were added before %s" % threshold
		old_notices = notification.Notice.objects.all()
		print "%s notices found" % len(old_notices)
		for n in old_notices:
			print n.added
		#healing = models.Stats.objects.filter(karma__lt=settings.KARMA_TO_JOIN).update(karma=F('karma') + 2)
		#msg = "Healed %s users" % healing
		#if healing > 0:
		#	logging.info(msg)
		#print msg
		
