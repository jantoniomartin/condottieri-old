from datetime import datetime, timedelta

from django.core.management.base import NoArgsCommand, CommandError

#from machiavelli import models
from condottieri_events import models

AGE=30*24*60*60

class Command(NoArgsCommand):
	"""
This script deletes all events in finished games that are older than AGE days.
	"""
	help = 'This command deletes all events in finished games that are older than AGE days.'

	def handle_noargs(self, **options):
		age = timedelta(0, AGE)
		threshold = datetime.now() - age
		print "Deleting events that were added before %s" % threshold
		old_events = models.BaseEvent.objects.filter(game__phase__exact=models.PHINACTIVE,
									game__slots__exact=0,
									game__last_phase_change__lt=threshold)
		print "%s events will be deleted" % len(old_events)
		old_events.delete()
