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

""" Django views definitions for machiavelli application. """

## stdlib
from datetime import datetime
from math import ceil

## django
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.db.models import Q, F
from django.views.decorators.cache import never_cache, cache_page
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

## machiavelli
from machiavelli.models import *
import machiavelli.utils as utils
import machiavelli.forms as forms

## condottieri_profiles
from condottieri_profiles.models import CondottieriProfile

## clones detection
if 'clones' in settings.INSTALLED_APPS:
	from clones import models as clones
else:
	clones = None

if "jogging" in settings.INSTALLED_APPS:
	from jogging import logging
else:
	logging = None

if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None


from machiavelli.models import Unit

def sidebar_context(request):
	context = {}
	context.update( {'activity': Player.objects.values("user").distinct().count()} )
	context.update( {'top_users': CondottieriProfile.objects.all().order_by('-total_score').select_related('user')[:5]} )
	return context

def summary(request):
	context = sidebar_context(request)
	context.update( {'forum': 'forum' in settings.INSTALLED_APPS} )
	if request.user.is_authenticated():
		joinable = Game.objects.exclude(player__user=request.user).filter(slots__gt=0).order_by('slots').select_related('scenario', 'configuration', 'player__user')
		my_games_ids = Game.objects.filter(player__user=request.user).values('id')
		context.update( {'revolutions': Revolution.objects.filter(opposition__isnull=True).exclude(government__game__id__in=my_games_ids).select_related('gorvernment__game__country')} )
		context.update( {'actions': Player.objects.filter(user=request.user, game__slots=0, done=False).select_related('game')} )
	else:
		joinable = Game.objects.filter(slots__gt=0).order_by('slots').select_related('scenario', 'configuration', 'player__user')
		context.update( {'revolutions': Revolution.objects.filter(opposition__isnull=True).select_related('government__game__country')} )
	if joinable:
		context.update( {'joinable_game': joinable[0]} )

	return render_to_response('machiavelli/summary.html',
							context,
							context_instance=RequestContext(request))

@never_cache
def my_active_games(request):
	""" Gets a paginated list of all the ongoing games in which the user is a player. """
	context = sidebar_context(request)
	if request.user.is_authenticated():
		my_players = Player.objects.filter(user=request.user, game__slots=0).select_related("country", "game__scenario", "game__configuration")
	else:
		my_players = Player.objects.none()
	paginator = Paginator(my_players, 10)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		player_list = paginator.page(page)
	except (EmptyPage, InvalidPage):
		player_list = paginator.page(paginator.num_pages)
	context.update( {
		'player_list': player_list,
		})

	return render_to_response('machiavelli/game_list_my_active.html',
							context,
							context_instance=RequestContext(request))

@never_cache
def other_active_games(request):
	""" Gets a paginated list of all the ongoing games in which the user is not a player """
	context = sidebar_context(request)
	if request.user.is_authenticated():
		games = Game.objects.exclude(phase=PHINACTIVE).exclude(player__user=request.user)
	else:
		games = Game.objects.exclude(phase=PHINACTIVE)
	paginator = Paginator(games, 10)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		game_list = paginator.page(page)
	except (EmptyPage, InvalidPage):
		game_list = paginator.page(paginator.num_pages)
	context.update( {
		'game_list': game_list,
		})

	return render_to_response('machiavelli/game_list_active.html',
							context,
							context_instance=RequestContext(request))



@never_cache
def finished_games(request, only_user=False):
	""" Gets a paginated list of the games that are finished """
	context = sidebar_context(request)
	games = Game.objects.filter(slots=0, phase=PHINACTIVE).order_by("-finished")
	if only_user:
		games = games.filter(score__user=request.user)
	paginator = Paginator(games, 10)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		game_list = paginator.page(page)
	except (EmptyPage, InvalidPage):
		game_list = paginator.page(paginator.num_pages)
	context.update( {
		'game_list': game_list,
		'only_user': only_user,
		})

	return render_to_response('machiavelli/game_list_finished.html',
							context,
							context_instance=RequestContext(request))

@never_cache
def joinable_games(request):
	""" Gets a paginated list of all the games that the user can join """
	context = sidebar_context(request)
	if request.user.is_authenticated():
		games = Game.objects.filter(slots__gt=0).exclude(player__user=request.user)
	else:
		games = Game.objects.filter(slots__gt=0)
	paginator = Paginator(games, 10)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		game_list = paginator.page(page)
	except (EmptyPage, InvalidPage):
		game_list = paginator.page(paginator.num_pages)
	context.update( {
		'game_list': game_list,
		'joinable': True,
		})

	return render_to_response('machiavelli/game_list_pending.html',
							context,
							context_instance=RequestContext(request))

@never_cache
@login_required
def pending_games(request):
	""" Gets a paginated list of all the games of the player that have not yet
	started """
	context = sidebar_context(request)
	games = Game.objects.filter(slots__gt=0, player__user=request.user)
	paginator = Paginator(games, 10)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		game_list = paginator.page(page)
	except (EmptyPage, InvalidPage):
		game_list = paginator.page(paginator.num_pages)
	context.update( {
		'game_list': game_list,
		'joinable': False,
		})

	return render_to_response('machiavelli/game_list_pending.html',
							context,
							context_instance=RequestContext(request))	

def base_context(request, game, player):
	context = {
		'user': request.user,
		'game': game,
		'map' : game.get_map_url(),
		'player': player,
		'player_list': game.player_list_ordered_by_cities(),
		'show_users': game.visible,
		}
	if game.slots > 0:
		context['player_list'] = game.player_set.filter(user__isnull=False)
	log = game.baseevent_set.all()
	if player:
		context['done'] = player.done
		if game.configuration.finances:
			context['ducats'] = player.ducats
		context['can_excommunicate'] = player.can_excommunicate()
		if game.slots == 0:
			context['time_exceeded'] = player.time_exceeded()
	log = log.exclude(season__exact=game.season,
							phase__exact=game.phase)
	if len(log) > 0:
		last_year = log[0].year
		last_season = log[0].season
		last_phase = log[0].phase
		context['log'] = log.filter(year__exact=last_year,
								season__exact=last_season,
								phase__exact=last_phase)
	else:
		context['log'] = log # this will always be an empty queryset
	#context['log'] = log[:10]
	rules = game.configuration.get_enabled_rules()
	if len(rules) > 0:
		context['rules'] = rules
		
	return context

#@never_cache
#def js_play_game(request, slug=''):
#	game = get_object_or_404(Game, slug=slug)
#	try:
#		player = Player.objects.get(game=game, user=request.user)
#	except:
#		player = Player.objects.none()
#	units = Unit.objects.filter(player__game=game)
#	player_list = game.player_list_ordered_by_cities()
#	context = {
#		'game': game,
#		'player': player,
#		'map': 'base-map.png',
#		'units': units,
#		'player_list': player_list,
#	}
#	return render_to_response('machiavelli/js_game.html',
#						context,
#						context_instance=RequestContext(request))
#

@never_cache
#@login_required
def play_game(request, slug='', **kwargs):
	game = get_object_or_404(Game, slug=slug)
	if game.slots == 0 and game.phase == PHINACTIVE:
		return redirect('game-results', slug=game.slug)
	try:
		player = Player.objects.get(game=game, user=request.user)
	except:
		player = Player.objects.none()
	if player:
		##################################
		## IP TRACKING FOR CLONES DETECTION
		if clones:
			if request.method == 'POST' and not request.is_ajax():
				try:
					fp = clones.Fingerprint(user=request.user,
											game=game,
											ip=request.META[settings.IP_HEADER])
					fp.save()
				except:
					pass
		##################################
		#if game.slots == 0:
		#	game.check_time_limit()
		if game.phase == PHINACTIVE:
			context = base_context(request, game, player)
			return render_to_response('machiavelli/inactive_actions.html',
							context,
							context_instance=RequestContext(request))
		elif game.phase == PHREINFORCE:
			if game.configuration.finances:
				return play_finance_reinforcements(request, game, player)
			else:
				return play_reinforcements(request, game, player)
		elif game.phase == PHORDERS:
			if 'extra' in kwargs and kwargs['extra'] == 'expenses':
				if game.configuration.finances:
					return play_expenses(request, game, player)
			return play_orders(request, game, player)
		elif game.phase == PHRETREATS:
			return play_retreats(request, game, player)
		else:
			raise Http404
	## no player
	else:
		context = base_context(request, game, player)
		return render_to_response('machiavelli/inactive_actions.html',
							context,
							context_instance=RequestContext(request))

def play_reinforcements(request, game, player):
	context = base_context(request, game, player)
	if player.done:
		context['to_place'] = player.unit_set.filter(placed=False)
		context['to_disband'] = player.unit_set.filter(placed=True, paid=False)
		context['to_keep'] = player.unit_set.filter(placed=True, paid=True)
	else:
		units_to_place = player.units_to_place()
		context['cities_qty'] = player.number_of_cities()
		context['cur_units'] = len(player.unit_set.all())
		if units_to_place > 0:
			## place units
			context['units_to_place'] = units_to_place
			ReinforceForm = forms.make_reinforce_form(player)
			ReinforceFormSet = formset_factory(ReinforceForm,
								formset=forms.BaseReinforceFormSet,
								extra=units_to_place)
			if request.method == 'POST':
				reinforce_form = ReinforceFormSet(request.POST)
				if reinforce_form.is_valid():
					for f in reinforce_form.forms:
						new_unit = Unit(type=f.cleaned_data['type'],
								area=f.cleaned_data['area'],
								player=player,
								placed=False)
						new_unit.save()
						#new_unit.place()
					#game.map_changed()
					## not sure, but i think i could remove the fol. line
					player = Player.objects.get(id=player.pk) ## see below
					player.end_phase()
					return HttpResponseRedirect(request.path)
			else:
				reinforce_form = ReinforceFormSet()
			context['reinforce_form'] = reinforce_form
		elif units_to_place < 0:
			## remove units
			DisbandForm = forms.make_disband_form(player)
			#choices = []
			context['units_to_disband'] = -units_to_place
			#for unit in player.unit_set.all():
			#	choices.append((unit.pk, unit))
			if request.method == 'POST':
				disband_form = DisbandForm(request.POST)
				if disband_form.is_valid():
					if len(disband_form.cleaned_data['units']) == -units_to_place:
						for u in disband_form.cleaned_data['units']:
							#u.delete()
							u.paid = False
							u.save()
						#game.map_changed()
						## odd: the player object needs to be reloaded or
						## the it doesn't know the change in game.map_outdated
						## this hack needs to be done in some other places
						player = Player.objects.get(id=player.pk)
						## --
						player.end_phase()
						return HttpResponseRedirect(request.path)
			else:
				disband_form = DisbandForm()
			context['disband_form'] = disband_form
	return render_to_response('machiavelli/reinforcements_actions.html',
							context,
							context_instance=RequestContext(request))

def play_finance_reinforcements(request, game, player):
	context = base_context(request, game, player)
	if player.done:
		context['to_place'] = player.unit_set.filter(placed=False)
		context['to_disband'] = player.unit_set.filter(placed=True, paid=False)
		context['to_keep'] = player.unit_set.filter(placed=True, paid=True)
		template_name = 'machiavelli/reinforcements_actions.html'
	else:
		step = player.step
		if step == 0:
			## the player must select the units that he wants to pay and keep
			UnitPaymentForm = forms.make_unit_payment_form(player)
			if request.method == 'POST':
				form = UnitPaymentForm(request.POST)
				if form.is_valid():
					cost = len(form.cleaned_data['units']) * 3
					if cost <= player.ducats:
						for u in form.cleaned_data['units']:
							u.paid = True
							u.save()
						player.ducats = player.ducats - cost
						step = 1
						player.step = step
						player.save()
						return HttpResponseRedirect(request.path)
			else:
				form = UnitPaymentForm()
			context['form'] = form
		elif step == 1:
			## the player can create new units if he has money and areas
			can_buy = player.ducats / 3
			can_place = player.get_areas_for_new_units(finances=True).count()
			max_units = min(can_buy, can_place)
			print "Max no of units is %s" % max_units
			ReinforceForm = forms.make_reinforce_form(player, finances=True)
			ReinforceFormSet = formset_factory(ReinforceForm,
								formset=forms.BaseReinforceFormSet,
								extra=max_units)
			if request.method == 'POST':
				formset = ReinforceFormSet(request.POST)
				if formset.is_valid():
					cost = 0
					for f in formset.forms:
						if 'area' in f.cleaned_data:
							new_unit = Unit(type=f.cleaned_data['type'],
									area=f.cleaned_data['area'],
									player=player,
									placed=False)
							new_unit.save()
							cost += 3
					player.ducats = player.ducats - cost
					player.save()
					player.end_phase()
					return HttpResponseRedirect(request.path)
			else:
				formset = ReinforceFormSet()
			context['formset'] = formset
			context['max_units'] = max_units
		else:
			raise Http404
		template_name = 'machiavelli/finance_reinforcements_%s.html' % step
	return render_to_response(template_name, context,
							context_instance=RequestContext(request))


def play_orders(request, game, player):
	context = base_context(request, game, player)
	#sent_orders = Order.objects.filter(unit__in=player.unit_set.all())
	sent_orders = player.order_set.all()
	context.update({'sent_orders': sent_orders})
	if game.configuration.finances:
		context['current_expenses'] = player.expense_set.all()
	if game.configuration.lenders:
		try:
			loan = player.loan
		except ObjectDoesNotExist:
			pass
		else:
			context.update({'loan': loan})
	if not player.done:
		OrderForm = forms.make_order_form(player)
		if request.method == 'POST':
			order_form = OrderForm(player, data=request.POST)
			if request.is_ajax():
				## validate the form
				clean = order_form.is_valid()
				response_dict = {'bad': 'false'}
				if not clean:
					response_dict.update({'bad': 'true'})
					d = {}
					for e in order_form.errors.iteritems():
						d.update({e[0] : unicode(e[1])})
					response_dict.update({'errs': d})
				else:
					#new_order = Order(**order_form.cleaned_data)
					#new_order.save()
					new_order = order_form.save()
					response_dict.update({'pk': new_order.pk ,
										'new_order': new_order.explain()})
				response_json = simplejson.dumps(response_dict, ensure_ascii=False)

				return HttpResponse(response_json, mimetype='application/javascript')
			## not ajax
			else:
				if order_form.is_valid():
					#new_order = Order(**order_form.cleaned_data)
					#new_order.save()
					new_order = order_form.save()
					return HttpResponseRedirect(request.path)
		else:
			order_form = OrderForm(player)
		context.update({'order_form': order_form})
	return render_to_response('machiavelli/orders_actions.html',
							context,
							context_instance=RequestContext(request))

@login_required
def delete_order(request, slug='', order_id=''):
	game = get_object_or_404(Game, slug=slug)
	player = get_object_or_404(Player, game=game, user=request.user)
	#order = get_object_or_404(Order, id=order_id, unit__player=player, confirmed=False)
	order = get_object_or_404(Order, id=order_id, player=player, confirmed=False)
	response_dict = {'bad': 'false',
					'order_id': order.id}
	try:
		order.delete()
	except:
		response_dict.update({'bad': 'true'})
	if request.is_ajax():
		response_json = simplejson.dumps(response_dict, ensure_ascii=False)
		return HttpResponse(response_json, mimetype='application/javascript')
		
	return redirect(game)

@login_required
def confirm_orders(request, slug=''):
	game = get_object_or_404(Game, slug=slug)
	player = get_object_or_404(Player, game=game, user=request.user, done=False)
	if request.method == 'POST':
		#sent_orders = Order.objects.filter(unit__in=player.unit_set.all())
		sent_orders = player.order_set.all()
		for order in sent_orders:
			if utils.order_is_possible(order):
				order.confirm()
				if logging:
					logging.info("Confirmed order %s" % order.format())
			else:
				if logging:
					logging.info("Deleting order %s" % order.format())
				#order.delete()
		player.end_phase()
	return redirect(game)		
	
def play_retreats(request, game, player):
	context = base_context(request, game, player)
	if not player.done:
		units = Unit.objects.filter(player=player).exclude(must_retreat__exact='')
		retreat_forms = []
		if request.method == 'POST':
			data = request.POST
			for u in units:
				unitid_key = "%s-unitid" % u.id
				area_key = "%s-area" % u.id
				unit_data = {unitid_key: data[unitid_key], area_key: data[area_key]}
				RetreatForm = forms.make_retreat_form(u)
				retreat_forms.append(RetreatForm(data, prefix=u.id))
			for f in retreat_forms:
				if f.is_valid():
					unitid = f.cleaned_data['unitid']
					area= f.cleaned_data['area']
					unit = Unit.objects.get(id=unitid)
					if isinstance(area, GameArea):
						print "%s will retreat to %s" % (unit, area)
						retreat = RetreatOrder(unit=unit, area=area)
					else:
						print "%s will disband" % unit
						retreat = RetreatOrder(unit=unit)
					retreat.save()
			player.end_phase()
			return HttpResponseRedirect(request.path)
		else:
			for u in units:
				RetreatForm = forms.make_retreat_form(u)
				retreat_forms.append(RetreatForm(prefix=u.id))
		if len(retreat_forms) > 0:
			context['retreat_forms'] = retreat_forms
	return render_to_response('machiavelli/retreats_actions.html',
							context,
							context_instance=RequestContext(request))

def play_expenses(request, game, player):
	context = base_context(request, game, player)
	context['current_expenses'] = player.expense_set.all()
	ExpenseForm = forms.make_expense_form(player)
	if request.method == 'POST':
		form = ExpenseForm(player, data=request.POST)
		if form.is_valid():
			expense = form.save()
			player.ducats = F('ducats') - expense.ducats
			player.save()
			return HttpResponseRedirect(request.path)
	else:
		form = ExpenseForm(player)

	context['form'] = form

	return render_to_response('machiavelli/expenses_actions.html',
							context,
							context_instance=RequestContext(request))

def game_error(request, game, message=''):
	try:
		player = Player.objects.get(game=game, user=request.user)
	except:
		player = Player.objects.none()
	context = base_context(request, game, player)
	context.update({'error': message })
	return render_to_response('machiavelli/game_error.html',
							context,
							context_instance=RequestContext(request))

#@login_required
#@cache_page(60 * 60) # cache 1 hour
def game_results(request, slug=''):
	game = get_object_or_404(Game, slug=slug)
	if game.phase != PHINACTIVE:
		raise Http404
	scores = game.score_set.filter(user__isnull=False).order_by('-points')
	context = {'game': game,
				'map' : game.get_map_url(),
				'players': scores,
				'show_log': False,}
	log = game.baseevent_set.all()
	if len(log) > 0:
		context['show_log'] = True
	return render_to_response('machiavelli/game_results.html',
							context,
							context_instance=RequestContext(request))

@never_cache
#@login_required
def logs_by_game(request, slug=''):
	game = get_object_or_404(Game, slug=slug)
	try:
		player = Player.objects.get(game=game, user=request.user)
	except:
		player = Player.objects.none()
	context = base_context(request, game, player)
	log_list = game.baseevent_set.all()
	log_list = log_list.exclude(season__exact=game.season,
						phase__exact=game.phase)
	paginator = Paginator(log_list, 25)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		log = paginator.page(page)
	except (EmptyPage, InvalidPage):
		log = paginator.page(paginator.num_pages)

	context['log'] = log 

	return render_to_response('machiavelli/log_list.html',
							context,
							context_instance=RequestContext(request))

@login_required
#@cache_page(60 * 60)
def create_game(request):
	## check minimum karma to create a game
	karma = request.user.get_profile().karma
	if karma < settings.KARMA_TO_JOIN:
		return low_karma_error(request)
	##
	context = sidebar_context(request)
	context.update( {'user': request.user,})
	if request.method == 'POST':
		game_form = forms.GameForm(request.user, data=request.POST)
		if game_form.is_valid():
			new_game = game_form.save(commit=False)
			new_game.slots = new_game.scenario.get_slots() - 1
			new_game.save()
			new_player = Player()
			new_player.user = request.user
			new_player.game = new_game
			new_player.save()
			config_form = forms.ConfigurationForm(request.POST,
												instance=new_game.configuration)
			config_form.save()
			## create the autonomous player
			#autonomous = Player(game=new_game, done=True)
			#autonomous.save()
			return redirect('summary')
	game_form = forms.GameForm(request.user)
	config_form = forms.ConfigurationForm()
	context['scenarios'] = Scenario.objects.filter(enabled=True)
	context['game_form'] = game_form
	context['config_form'] = config_form
	return render_to_response('machiavelli/game_form.html',
							context,
							context_instance=RequestContext(request))

@login_required
def join_game(request, slug=''):
	g = get_object_or_404(Game, slug=slug)
	karma = request.user.get_profile().karma
	if karma < settings.KARMA_TO_JOIN:
		return low_karma_error(request)
	if g.slots > 0:
		try:
			Player.objects.get(user=request.user, game=g)
		except:
			## the user is not in the game
			new_player = Player(user=request.user, game=g)
			new_player.save()
			g.player_joined()
	return redirect('summary')

@login_required
def leave_game(request, slug=''):
	g = get_object_or_404(Game, slug=slug)
	if g.slots > 0:
		try:
			player = Player.objects.get(user=request.user, game=g)
		except:
			## the user is not in the game
			raise Http404
		else:
			player.delete()
			g.slots += 1
			g.save()
	else:
		## you cannot leave a game that has already started
		raise Http404
	return redirect('summary')

@login_required
def overthrow(request, revolution_id):
	revolution = get_object_or_404(Revolution, pk=revolution_id)
	g = revolution.government.game
	try:
		## check that overthrowing user is not a player
		Player.objects.get(user=request.user, game=g)
	except ObjectDoesNotExist:
		try:
			## check that there is not another revolution with the same player
			Revolution.objects.get(government__game=g, opposition=request.user)
		except ObjectDoesNotExist:
			karma = request.user.get_profile().karma
			if karma < settings.KARMA_TO_JOIN:
				return low_karma_error(request)
			revolution.opposition = request.user
			revolution.save()
			return redirect('summary')
		else:
			raise Http404
	else:
		raise Http404

@login_required
def excommunicate(request, slug, player_id):
	game = get_object_or_404(Game, slug=slug)
	if game.phase == 0 or not game.configuration.excommunication:
		return game_error(request, game, _("You cannot excommunicate in this game."))
	player = get_object_or_404(Player, id=player_id,
								game=game,
								excommunicated__isnull=True,
								country__can_excommunicate=False)
	papacy = get_object_or_404(Player, user=request.user,
								game=game,
								country__can_excommunicate=True)
	## check if someone has been excommunicated this year
	if papacy.can_excommunicate():
		player.excommunicate()
	else:
		## a player has been already excommunicated this year
		return game_error(request, game, _("You have already excommunicated a country this year."))
	return redirect(game)

@login_required
def reset_excommunications(request, slug):
	game = get_object_or_404(Game, slug=slug)
	if game.phase == 0 or not game.configuration.excommunication:
		return game_error(request, game, _("Excommunications cannot be reset."))
	player = get_object_or_404(Player, game=game, user=request.user)
	if not player.can_excommunicate():
		return game_error(request, game, _("You are not allowed to forgive excommunications."))
	game.player_set.all().update(excommunicated=None)
	return redirect(game)


#@cache_page(60 * 60)
def scenario_list(request):
	""" Gets a list of all the enabled scenarios. """
	context = sidebar_context(request)	
	scenarios = Scenario.objects.filter(enabled=True)
	context.update( {'scenarios': scenarios, })

	return render_to_response('machiavelli/scenario_list.html',
							context,
							context_instance = RequestContext(request))

#@cache_page(60 * 60)
def show_scenario(request, scenario_id):
	scenario = get_object_or_404(Scenario, id=scenario_id, enabled=True)

	countries = Country.objects.filter(home__scenario=scenario).distinct()
	autonomous = Setup.objects.filter(scenario=scenario, country__isnull=True)
	mayor_cities = scenario.cityincome_set.all()

	countries_dict = {}

	for c in countries:
		data = {}
		data['name'] = c.name
		data['homes'] = c.home_set.filter(scenario=scenario)
		data['setups'] = c.setup_set.filter(scenario=scenario)
		treasury = c.treasury_set.get(scenario=scenario)
		data['ducats'] = treasury.ducats
		data['double'] = treasury.double
		countries_dict[c.static_name] = data

	return render_to_response('machiavelli/scenario_detail.html',
							{'scenario': scenario,
							'countries': countries_dict,
							'autonomous': autonomous,
							'mayor_cities': mayor_cities,},
							context_instance=RequestContext(request))


#@login_required
#@cache_page(30 * 60)
def hall_of_fame(request):
	profiles_list = CondottieriProfile.objects.all().order_by('-total_score')
	paginator = Paginator(profiles_list, 10)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		profiles = paginator.page(page)
	except (EmptyPage, InvalidPage):
		profiles = paginator.page(paginator.num_pages)
	context = {'profiles': profiles}
	return render_to_response('machiavelli/hall_of_fame.html',
							context,
							context_instance=RequestContext(request))

def ranking(request, key='', val=''):
	""" Gets the qualification, ordered by scores, for a given parameter. """
	
	scores = Score.objects.all().order_by('-points')
	if key == 'user': # by user
		user = get_object_or_404(User, username=val)
		scores = scores.filter(user=user)
		title = _("Ranking for the user") + ' ' + val
	elif key == 'scenario': # by scenario
		scenario = get_object_or_404(Scenario, name=val)
		scores = scores.filter(game__scenario=scenario)
		title = _("Ranking for the scenario") + ' ' + val
	elif key == 'country': # by country
		country = get_object_or_404(Country, css_class=val)
		scores = scores.filter(country=country)
		title = _("Ranking for the country") + ' ' + country.name
	else:
		raise Http404

	paginator = Paginator(scores, 10)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		qualification = paginator.page(page)
	except (EmptyPage, InvalidPage):
		qualification = paginator.page(paginator.num_pages)
	context = {
		'qualification': qualification,
		'key': key,
		'val': val,
		'title': title,
		}
	return render_to_response('machiavelli/ranking.html',
							context,
							context_instance=RequestContext(request))


@login_required
#@cache_page(120 * 60) # cache 2 hours
def low_karma_error(request):
	context = {
		'karma': request.user.get_profile().karma,
		'minimum': settings.KARMA_TO_JOIN,
	}
	return render_to_response('machiavelli/low_karma.html',
							context,
							context_instance=RequestContext(request))

@login_required
#@cache_page(60 * 60) # cache 1 hour
def turn_log_list(request, slug=''):
	game = get_object_or_404(Game, slug=slug)
	log_list = game.turnlog_set.all()
	paginator = Paginator(log_list, 1)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		log = paginator.page(page)
	except (EmptyPage, InvalidPage):
		log = paginator.page(paginator.num_pages)
	context = {
		'game': game,
		'log': log,
		}

	return render_to_response('machiavelli/turn_log_list.html',
							context,
							context_instance=RequestContext(request))

@login_required
def give_money(request, slug, player_id):
	game = get_object_or_404(Game, slug=slug)
	if game.phase == 0 or not game.configuration.finances:
		return game_error(request, game, _("You cannot give money in this game."))
	borrower = get_object_or_404(Player, id=player_id, game=game)
	lender = get_object_or_404(Player, user=request.user, game=game)
	context = base_context(request, game, lender)

	if request.method == 'POST':
		form = forms.LendForm(request.POST)
		if form.is_valid():
			ducats = form.cleaned_data['ducats']
			if ducats > lender.ducats:
				return game_error(request, game, _("You cannot give more money than you have"))
			lender.ducats = F('ducats') - ducats
			borrower.ducats = F('ducats') + ducats
			lender.save()
			borrower.save()
			if notification:
				extra_context = {'game': lender.game,
								'ducats': ducats,
								'country': lender.country}
				notification.send([borrower.user,], "received_ducats", extra_context , on_site=True)
			return redirect('show-game', slug=slug)
	else:
		form = forms.LendForm()
	context['form'] = form
	context['borrower'] = borrower

	return render_to_response('machiavelli/give_money.html',
							context,
							context_instance=RequestContext(request))

@login_required
def borrow_money(request, slug):
	game = get_object_or_404(Game, slug=slug)
	player = get_object_or_404(Player, user=request.user, game=game)
	if game.phase != PHORDERS or not game.configuration.lenders or player.done:
		return game_error(request, game, _("You cannot borrow money in this moment."))
	context = base_context(request, game, player)
	credit = player.get_credit()
	try:
		loan = player.loan
	except ObjectDoesNotExist:
		## the player may ask for a loan
		if request.method == 'POST':
			form = forms.BorrowForm(request.POST)
			if form.is_valid():
				ducats = form.cleaned_data['ducats']
				term = int(form.cleaned_data['term'])
				if ducats > credit:
					return game_error(request, game, _("You cannot borrow so much money."))
				loan = Loan(player=player, season=game.season)
				if term == 1:
					loan.debt = int(ceil(ducats * 1.2))
				elif term == 2:
					loan.debt = int(ceil(ducats * 1.5))
				else:
					return game_error(request, game, _("The chosen term is not valid."))
				loan.year = game.year + term
				loan.save()
				player.ducats = F('ducats') + ducats
				player.save()
				return redirect('show-game', slug=slug)
		else:
			form = forms.BorrowForm()
	else:
		## the player must repay a loan
		context.update({'loan': loan})
		if request.method == 'POST':
			if player.ducats >= loan.debt:
				player.ducats = F('ducats') - loan.debt
				player.save()
				loan.delete()
				return redirect('show-game', slug=slug)
			else:
				return game_error(request, game, _("You don't have enough money to repay the loan."))
		else:
			form = forms.RepayForm()
	context.update({'credit': credit,
					'form': form,})

	return render_to_response('machiavelli/borrow_money.html',
							context,
							context_instance=RequestContext(request))
