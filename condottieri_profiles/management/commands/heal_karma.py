from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings
from django.db.models import F

from jogging import logging

if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None

from condottieri_profiles import models

class Command(NoArgsCommand):
	"""
This script 'heals' the users that have less than the minimum karma to
join a game.
	"""
	help = 'This command heals the users that have less than the minimum karma to join a game.'

	def handle_noargs(self, **options):
		to_heal = models.CondottieriProfile.objects.filter(karma__lt=settings.KARMA_TO_JOIN)
		for profile in to_heal:
			profile.karma += 2
			profile.save()
			if profile.karma >= settings.KARMA_TO_JOIN:
				if notification:
					notification.send([profile.user,], "karma_healed", {}, True)
		msg = "Healed karma to %s users" % len(to_heal)
		if len(to_heal) > 0:
			logging.info(msg)
		
