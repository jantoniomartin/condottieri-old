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
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.conf import global_settings

from messages.utils import format_quote
from messages.models import Message

from django.contrib import messages

from machiavelli.models import Player, Game
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
	elif sender_player.may_excommunicate and recipient_player.is_excommunicated:
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
		messages.error(request, e.value)
		return redirect(game)
	## try to find a common language for the two players
	common_language_code = None
	sender_lang = sender_player.user.get_profile().spokenlanguage_set.values_list('code', flat=True)
	recipient_lang = recipient_player.user.get_profile().spokenlanguage_set.values_list('code', flat=True)
	for lang in sender_lang:
		if lang in recipient_lang:
			common_language_code = lang
			break
	if common_language_code is not None:
		lang_dict = dict(global_settings.LANGUAGES)
		if common_language_code in lang_dict.keys():
			common_language = lang_dict[common_language_code]
		context.update({'common_language': common_language })
	if request.method == 'POST':
		letter_form = forms.LetterForm(sender_player, recipient_player, data=request.POST)
		if letter_form.is_valid():
			letter = letter_form.save()
			messages.success(request, _("The letter has been successfully sent."))
			## check if sender must be excommunicated
			if not sender_player.is_excommunicated and recipient_player.is_excommunicated:
				sender_player.set_excommunication(by_pope=False)
				messages.info(request, _("You have been excommunicated."))
			return redirect(game)
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
		if not sender_player.is_excommunicated and recipient_player.is_excommunicated:
			context['excom_notice'] = True
		if sender_player.is_excommunicated and not recipient_player.is_excommunicated:
			messages.error(request, _("You can write letters only to other excommunicated countries."))
			return redirect(game)
	
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

@login_required
def inbox(request, slug=None):
	"""
	Displays a list of received messages for the current user.
	Optional Arguments:
	``slug``: show only messages of the game with this name.
	"""
	context = {}
	message_list = Message.objects.inbox_for(request.user)
	if slug:
		game = get_object_or_404(Game, slug=slug)
		message_list = message_list.filter(letter__sender_player__game=game)
		context['game'] = game
	context['message_list'] = message_list
	return render_to_response('condottieri_messages/inbox.html',
   	    					context,
							context_instance=RequestContext(request))

@login_required
def outbox(request, slug=None):
	"""
	Displays a list of sent messages by the current user.
	Optional arguments:
	``slug``: show only messages of the game with this name.
	"""
	context = {}
	message_list = Message.objects.outbox_for(request.user)
	if slug:
		game = get_object_or_404(Game, slug=slug)
		message_list = message_list.filter(letter__sender_player__game=game)
		context['game'] = game
	context['message_list'] = message_list
	return render_to_response('condottieri_messages/outbox.html',
   	    					context,
							context_instance=RequestContext(request))

##
## 'delete' and 'undelete' code is taken from django-messages and modified
## to disable notifications when a message is deleted or recovered
##

@login_required
def delete(request, message_id, success_url=None):
    """
    Marks a message as deleted by sender or recipient. The message is not
    really removed from the database, because two users must delete a message
    before it's save to remove it completely. 
    A cron-job should prune the database and remove old messages which are 
    deleted by both users.
    As a side effect, this makes it easy to implement a trash with undelete.
    
    You can pass ?next=/foo/bar/ via the url to redirect the user to a different
    page (e.g. `/foo/bar/`) than ``success_url`` after deletion of the message.
    """
    user = request.user
    now = datetime.datetime.now()
    message = get_object_or_404(Message, id=message_id)
    deleted = False
    if success_url is None:
        success_url = reverse('messages_inbox')
    if request.GET.has_key('next'):
        success_url = request.GET['next']
    if message.sender == user:
        message.sender_deleted_at = now
        deleted = True
    if message.recipient == user:
        message.recipient_deleted_at = now
        deleted = True
    if deleted:
        message.save()
        messages.success(request, _(u"Message successfully deleted."))
        #if notification:
        #    notification.send([user], "messages_deleted", {'message': message,})
        return HttpResponseRedirect(success_url)
    raise Http404

@login_required
def undelete(request, message_id, success_url=None):
    """
    Recovers a message from trash. This is achieved by removing the
    ``(sender|recipient)_deleted_at`` from the model.
    """
    user = request.user
    message = get_object_or_404(Message, id=message_id)
    undeleted = False
    if success_url is None:
        success_url = reverse('messages_inbox')
    if request.GET.has_key('next'):
        success_url = request.GET['next']
    if message.sender == user:
        message.sender_deleted_at = None
        undeleted = True
    if message.recipient == user:
        message.recipient_deleted_at = None
        undeleted = True
    if undeleted:
        message.save()
        messages.success(request, _(u"Message successfully recovered."))
        #if notification:
        #    notification.send([user], "messages_recovered", {'message': message,})
        return HttpResponseRedirect(success_url)
    raise Http404

