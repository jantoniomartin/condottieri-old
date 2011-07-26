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

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from messages import models as messages
from machiavelli.models import Player, SEASONS
from machiavelli.signals import government_overthrown

if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None

class Letter(messages.Message):
	""" Letter is just a django-messages Message that adds two fields: sender_player and
	recipient_player. """
	sender_player = models.ForeignKey(Player, related_name='sent_messages', verbose_name=_("From country"))
	recipient_player = models.ForeignKey(Player, related_name='received_messages', verbose_name=_("To country"))
	year = models.PositiveIntegerField(default=0)
	season = models.PositiveIntegerField(default=1, choices=SEASONS)
    
	def get_absolute_url(self):
		return ('condottieri_messages_detail', [self.id])
	get_absolute_url = models.permalink(get_absolute_url)

def notify_new_letter(sender, instance, created, **kw):
	if notification and isinstance(instance, Letter) and created:
		user = [instance.recipient,]
		game = instance.recipient_player.game
		extra_context = {'game': game,
						'letter': instance }
		if game.fast:
			notification.send_now(user, "condottieri_messages_received", extra_context)
		else:
			notification.send(user, "condottieri_messages_received", extra_context)

models.signals.post_save.connect(notify_new_letter, sender=Letter)

def update_letter_users(sender, **kwargs):
	assert isinstance(sender, Player), "sender must be a Player"
	Letter.objects.filter(sender_player=sender).update(sender=sender.user)
	Letter.objects.filter(recipient_player=sender).update(recipient=sender.user)

government_overthrown.connect(update_letter_users)

