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
from machiavelli.models import Player

if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None

class Letter(messages.Message):
	""" Letter is just a django-messages Message that adds two fields: sender_player and
	recipient_player. """
	sender_player = models.ForeignKey(Player, related_name='sent_messages', verbose_name=_("From country"))
	recipient_player = models.ForeignKey(Player, related_name='received_messages', verbose_name=_("To country"))
    
	def get_absolute_url(self):
		return ('condottieri_messages_detail', [self.id])
	get_absolute_url = models.permalink(get_absolute_url)

def notify_new_letter(sender, instance, created, **kw):
	print "Wondering if a notice should be sent\n\n"
	if notification and isinstance(instance, Letter) and created:
		print "Sending notice\n\n"
		user = [instance.recipient,]
		extra_context = {'game': instance.recipient_player.game,
						'letter': instance }
		notification.send(user, "condottieri_messages_received", extra_context , on_site=False)

#models.signals.post_save.connect(notify_new_letter, sender=Letter)

