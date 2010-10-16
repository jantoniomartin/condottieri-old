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
##
## AUTHOR: Jose Antonio Martin <jantonio.martin AT gmail DOT com>

""" This application is meant to substitute the profiles in Pinax, so that the
profiles hold more information related to the game, such as scores, and karma.

"""

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings


KARMA_MINIMUM = settings.KARMA_MINIMUM
KARMA_DEFAULT = settings.KARMA_DEFAULT
KARMA_MAXIMUM = settings.KARMA_MAXIMUM


class CondottieriProfile(models.Model):
	""" Defines the actual profile for a Condottieri user.

	"""
	user = models.ForeignKey(User, unique=True, verbose_name=_('user'))
	""" A User object related to the profile """
	name = models.CharField(_('name'), max_length=50, null=True, blank=True)
	""" The user complete name """
	about = models.TextField(_('about'), null=True, blank=True)
	""" More user info """
	location = models.CharField(_('location'), max_length=40, null=True, blank=True)
	""" Geographic location string """
	karma = models.PositiveIntegerField(default=KARMA_DEFAULT, editable=False)
	""" Total karma value """
	total_score = models.PositiveIntegerField(default=0, editable=False)
	""" Sum of game scores """

	def __unicode__(self):
		return self.user.username

	def get_absolute_url(self):
		return ('profile_detail', None, {'username': self.user.username})
	get_absolute_url = models.permalink(get_absolute_url)
	
	def adjust_karma(self, k):
		""" Adds or substracts some karma to the total """
		if not isinstance(k, int):
			return
		new_karma = self.karma + k
		if new_karma > KARMA_MAXIMUM:
			new_karma = KARMA_MAXIMUM
		elif new_karma < KARMA_MINIMUM:
			new_karma = KARMA_MINIMUM
		self.karma = new_karma
		self.save()

def create_profile(sender, instance=None, **kwargs):
	""" Creates a profile associated to a User	"""
	if instance is None:
		return
	profile, created = CondottieriProfile.objects.get_or_create(user=instance)

post_save.connect(create_profile, sender=User)
