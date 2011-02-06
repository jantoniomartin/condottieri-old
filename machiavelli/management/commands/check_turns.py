from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

from jogging import logging

from machiavelli import models

class Command(NoArgsCommand):
	"""
This script checks in every active game if the current turn must change. This happens either
when all the players have finished OR the time limit is exceeded
	"""
	help = 'This script checks in every active game if the current turn must change. \
	This happens either when all the players have finished OR the time limit is exceeded.'

	def handle_noargs(self, **options):
		active_games = models.Game.objects.exclude(phase=0)
		for game in active_games:
			game.check_finished_phase()
