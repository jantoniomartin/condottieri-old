## Copyright (c) 2011 by Jose Antonio Martin <jantonio.martin AT gmail DOT com>
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU Affero General Public License as published by the
## Free Software Foundation, either version 3 of the License, or (at your option
## any later version.
##
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
## for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.
##
## This license is also included in the file COPYING
##
## AUTHOR: Jose Antonio Martin <jantonio.martin AT gmail DOT com>

""" Definitions for common classes that are related to more than one app

"""

from django.db import models
from django.conf import settings

from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

if "jogging" in settings.INSTALLED_APPS:
	from jogging import logging
else:
	logging = None

from machiavelli.signals import game_finished

class Server(models.Model):
	""" Defines core attributes for the whole site """
	ranking_last_update = models.DateTimeField()
	ranking_outdated = models.BooleanField(default=False)

	def __unicode__(self):
		return "Server %s" % self.pk

def outdate_ranking(sender, **kwargs):
	try:
		server = Server.objects.get()
	except MultipleObjectsReturned:
		if logging:
			logging.error("Multiple servers found")
	except ObjectDoesNotExist:
		if logging:
			logging.error("No configured server")
	else:
		server.ranking_outdated = True
		server.save()

game_finished.connect(outdate_ranking)
