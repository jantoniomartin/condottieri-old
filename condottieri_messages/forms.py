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

import django.forms as forms

from condottieri_messages.models import *

class LetterForm(forms.ModelForm):
	def __init__(self, sender_player, recipient_player, **kwargs):
		super(LetterForm, self).__init__(**kwargs)
		self.instance.sender_player = sender_player
		self.instance.recipient_player = recipient_player
		self.instance.sender = sender_player.user
		self.instance.recipient = recipient_player.user
		self.instance.year = sender_player.game.year
		self.instance.season = sender_player.game.season

	class Meta:
		model = Letter
		fields = ('subject', 'body',)

