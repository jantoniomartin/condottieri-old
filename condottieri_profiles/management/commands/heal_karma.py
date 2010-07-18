from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from django.db.models import F

from jogging import logging

from condottieri_profiles import models

class Command(NoArgsCommand):
	"""
This script 'heals' the users that have less than the minimum karma to
join a game.
	"""
	help = 'This command heals the users that have less than the minimum karma to join a game.'

	def handle_noargs(self, **options):
		healing = models.CondottieriProfile.objects.filter(karma__lt=settings.KARMA_TO_JOIN).update(karma=F('karma') + 2)
		msg = "Healed %s users" % healing
		if healing > 0:
			logging.info(msg)
		print msg
		
