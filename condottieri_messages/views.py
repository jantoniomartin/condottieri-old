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

import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import Http404
from django.template import RequestContext
from django.utils.translation import ugettext as _

from messages.utils import format_quote

from machiavelli.models import Player
from machiavelli.views import base_context, game_error

from condottieri_messages.exceptions import LetterError

import condottieri_messages.forms as forms
from condottieri_messages.models import Letter

def check_errors(request, game, sender_player, recipient_player):
	msg = None
	if sender_player.eliminated or recipient_player.eliminated:
		msg = _("Eliminated players cannot send or receive letters")
	## if the game is inactive, return 404 error
	elif game.phase == 0:
		msg = _("You cannot send letters in an inactive game.")
	## check if the sender has excommunicated the recipient
	elif sender_player.country.can_excommunicate and recipient_player.excommunicated:
		msg = _("You cannot write to a country that you have excommunicated.")
	else:
		return True
	raise LetterError(msg)

@login_required
def compose(request, sender_id=None, recipient_id=None, letter_id=None):
	if sender_id and recipient_id:
		## check that the sender is legitimate
		sender_player = get_object_or_404(Player, user=request.user, id=sender_id)
		game = sender_player.game
		recipient_player = get_object_or_404(Player, id=recipient_id, game=game)
		parent = Letter.objects.none()
	elif letter_id:
		parent = get_object_or_404(Letter, id=letter_id)
		if parent.sender != request.user and parent.recipient != request.user:
			raise Http404
		sender_player = parent.recipient_player
		recipient_player = parent.sender_player
		game = sender_player.game
	else:
		raise Http404
	context = base_context(request, game, sender_player)
	try:
		check_errors(request, game, sender_player, recipient_player)
	except LetterError, e:
		return game_error(request, game, e.value)	
	if request.method == 'POST':
		letter_form = forms.LetterForm(sender_player, recipient_player, data=request.POST)
		if letter_form.is_valid():
			letter = letter_form.save()
			## check if sender must be excommunicated
			if not sender_player.excommunicated and recipient_player.excommunicated:
				sender_player.excommunicate(year=recipient_player.excommunicated)
			return redirect('show-game', slug=game.slug)
	else:
		if parent:
			initial = {'body': _(u"%(sender)s wrote:\n%(body)s") % {
					'sender': parent.sender_player.country, 
					'body': format_quote(parent.body)}, 
					'subject': _(u"Re: %(subject)s") % {'subject': parent.subject},
					}
		else:
			initial = {}
		letter_form = forms.LetterForm(sender_player,
									recipient_player,
									initial=initial)
		if not sender_player.excommunicated and recipient_player.excommunicated:
			context['excom_notice'] = True
		if sender_player.excommunicated and not recipient_player.excommunicated:
			return game_error(request, game, _("You can write letters only to other excommunicated countries."))
	
	context.update({'form': letter_form,
					'sender_player': sender_player,
					'recipient_player': recipient_player,
					})

	return render_to_response('condottieri_messages/compose.html',
							context,
							context_instance=RequestContext(request))

@login_required
def view(request, message_id):
	"""
	Modified version of condottieri-messages view.
	Shows a single message.``message_id`` argument is required.
	The user is only allowed to see the message, if he is either 
	the sender or the recipient. If the user is not allowed a 404
	is raised. 
	If the user is the recipient and the message is unread 
	``read_at`` is set to the current datetime.
	"""
	user = request.user
	now = datetime.datetime.now()
	message = get_object_or_404(Letter, id=message_id)
	if (message.sender != user) and (message.recipient != user):
		raise Http404
	game = message.sender_player.game
	player = Player.objects.get(user=request.user, game=game)
	context = base_context(request, game, player)
	if message.read_at is None and message.recipient == user:
		message.read_at = now
		message.save()
	context.update({'message' : message,})
	return render_to_response('condottieri_messages/view.html', 
							context,
							context_instance=RequestContext(request))
