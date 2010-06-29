## Copyright (c) 2010 by Jose Antonio Martin <jantonio.martin AT gmail DOT com>
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

## django
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

## machiavelli
from machiavelli.models import Game

class Fingerprint(models.Model):
	user = models.ForeignKey(User)
	game = models.ForeignKey(Game)
	ip = models.IPAddressField()
	timestamp = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		return "%s(%s) IP:%s" % (self.user, self.game, self.ip)

class Clone(models.Model):
	original = models.ForeignKey(User, related_name='original')
	fake = models.ForeignKey(User, related_name='fake')
	timestamps = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		return "%s is a clone of %s" % (self.fake, self.original)

	class Meta:
		unique_together = (('original', 'fake'),)

