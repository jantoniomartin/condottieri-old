from datetime import datetime, timedelta

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

if "jogging" in settings.INSTALLED_APPS:
	from jogging import logging
else:
	logging = None

from condottieri_common.models import Server
import condottieri_profiles.models as profiles
import machiavelli.models as machiavelli

deval = settings.SCORE_DEVALUATION
threshold = timedelta(30 * settings.DEVALUATION_MONTHS)


class Command(NoArgsCommand):
	"""
	This command calculates the weighted scores of all the profiles.
	"""
	help = "Calculates the weighted scores of all the profiles"

	def handle_noargs(self, **options):
		## check first if the ranking is outdated
		server = Server.objects.get()
		if not server.ranking_outdated:
			return

		profile_list = profiles.CondottieriProfile.objects.filter(total_score__gt=0)
		last_game = machiavelli.Game.objects.order_by('-finished')[0]
		now = last_game.finished
		msg = "Recalculating weighted scores\n"
		msg += "Reference date: %s\n" % now
		msg += "Found %s profiles\n" % profile_list.count()
		c = 0
		for p in profile_list:
			scores = machiavelli.Score.objects.filter(user=p.user)
			weighted = 0
			for s in scores:
				age = now - s.created_at
				if age <= threshold:
					months = age.days / 30
				else:
					months = threshold.days / 30
				factor = 1.0 - ( months * deval )
				w = s.points * factor
				weighted += w
			p.weighted_score = int(round(weighted))
			p.save()
			c += 1
		msg += "Processed %s profiles\n" % c

		server.ranking_last_update = datetime.now()
		server.ranking_outdated = False
		server.save()
		msg += "Server updated\n"

		if logging:
			logging.info(msg)
		else:
			print msg

