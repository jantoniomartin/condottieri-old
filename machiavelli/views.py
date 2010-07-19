## stdlib
import thread

## django
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.forms.formsets import formset_factory
from django.db.models import Q, Sum
from django.views.decorators.cache import never_cache, cache_page
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings

## machiavelli
from machiavelli.models import *
import machiavelli.utils as utils
import machiavelli.forms as forms
import machiavelli.graphics as graphics

## condottieri_profiles
from condottieri_profiles.models import CondottieriProfile

## condottieri_events
from condottieri_events.models import OrderEvent

## clones detection
if 'clones' in settings.INSTALLED_APPS:
	from clones import models as clones
else:
	clones = None

#@login_required
def game_list(request):
	active_games = Game.objects.exclude(slots=0, phase=PHINACTIVE)
	finished_games = Game.objects.filter(slots=0, phase=PHINACTIVE)
	if request.user.is_authenticated():
		other_games = active_games.exclude(player__user=request.user)
		your_games = active_games.filter(player__user=request.user)
	else:
		other_games = active_games
		your_games = Game.objects.none()
	revolutions = []
	for r in Revolution.objects.filter(opposition__isnull=True):
		if r.government.game in other_games:
			revolutions.append(r)
	context = {
		'your_games': your_games,
		'other_games': other_games,
		'finished_games': finished_games,
		'revolutions': revolutions,
		'user': request.user,
	}

	return render_to_response('machiavelli/game_list.html',
							context,
							context_instance=RequestContext(request))

def base_context(request, game, player):
	context = {
		'user': request.user,
		'game': game,
		'map' : game.get_map_url(),
		'player': player,
		'player_list': game.player_list_ordered_by_cities(),
		}
	log = game.baseevent_set.all()
	if player:
		#context['phase_partial'] = "machiavelli/phase_%s.html" % game.phase
		#context['inbox'] = player.received.order_by('-id')[:10]
		context['inbox_all'] = player.received.all().count()
		context['inbox_unread'] = player.received.filter(read=False).count()
		context['outbox_all'] = player.sent.all().count()
		context['outbox_unread'] = player.sent.filter(read=False).count()
		context['done'] = player.done
		context['can_excommunicate'] = player.can_excommunicate()
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

@never_cache
#@login_required
def play_game(request, slug=''):
	game = get_object_or_404(Game, slug=slug)
	try:
		player = Player.objects.get(game=game, user=request.user)
	except:
		player = Player.objects.none()
	context = base_context(request, game, player)
	if game.slots == 0 and game.phase == PHINACTIVE:
		return redirect('game-results', slug=game.slug)
	if player:
		##################################
		## IP TRACKING FOR CLONES DETECTION
		if clones:
			if request.method == 'POST':
				try:
					fp = clones.Fingerprint(user=request.user,
											game=game,
											ip=request.META[settings.IP_HEADER])
					fp.save()
				except:
					pass
		##################################
		if game.slots == 0:
			game.check_time_limit()
		if game.phase == PHINACTIVE:
			return render_to_response('machiavelli/inactive_actions.html',
							context,
							context_instance=RequestContext(request))
		elif game.phase == PHREINFORCE:
			return play_reinforcements(request, game, player)
		elif game.phase == PHORDERS:
			if player.done:
				orders = OrderEvent.objects.filter(game=game, year=game.year,
											season=game.season,
											phase=game.phase,
											country=player.country)
				context['orders'] = orders	
			return play_orders(request, game, player)
		elif game.phase == PHRETREATS:
			return play_retreats(request, game, player)
		else:
			raise Http404
	## no player
	else:
		return render_to_response('machiavelli/inactive_actions.html',
							context,
							context_instance=RequestContext(request))

def play_reinforcements(request, game, player):
	context = base_context(request, game, player)
	if not player.done:
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
								player=player)
						new_unit.place()
					#game.map_changed()
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
							u.delete()
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

def play_orders(request, game, player):
	## receiving orders
	context = base_context(request, game, player)
	if player.done:
		orders = OrderEvent.objects.filter(game=game, year=game.year,
									season=game.season,
									phase=game.phase,
									country=player.country)
		context['orders'] = orders
	else:
		OrderForm = forms.make_jsorder_form(player)
		n_forms = player.unit_set.count()
		OrderFormSet = formset_factory(OrderForm, formset=forms.BaseOrderFormSet, extra=n_forms)
		if request.method == 'POST':
			orders_formset = OrderFormSet(request.POST)
			if orders_formset.is_valid():
				for form in orders_formset.forms:
					new_order = utils.parse_order_form(form.cleaned_data)
					if isinstance(new_order, Order):
						if not new_order.code == 'H':
							new_order.save()
				player.end_phase()
				return HttpResponseRedirect(request.path)
		else:
			orders_formset = OrderFormSet()
		context['orders_formset'] = orders_formset
	return render_to_response('machiavelli/orders_actions.html',
							context,
							context_instance=RequestContext(request))

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

#@login_required
@cache_page(60 * 60) # cache 1 hour
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
@cache_page(60 * 60)
def create_game(request):
	## check minimum karma to create a game
	karma = request.user.get_profile().karma
	if karma < settings.KARMA_TO_JOIN:
		return low_karma_error(request)
	##
	context = {'user': request.user,}
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
			return redirect('game-list')
	else:
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
	return redirect('game-list')

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
	return redirect('game-list')

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
			return redirect('game-list')
		else:
			raise Http404
	else:
		raise Http404

@never_cache
@login_required
def box_list(request, slug='', box='inbox'):
	game = get_object_or_404(Game, slug=slug)
	player = get_object_or_404(Player, game=game, user=request.user)
	context = base_context(request, game, player)
	context['box'] = box

	if box == 'inbox':
		letter_list = player.received.order_by('-id')
	elif box == 'outbox':
		letter_list = player.sent.order_by('-id')
	else:
		letter_list = Letter.objects.none()
	
	paginator = Paginator(letter_list, 10)
	try:
		page = int(request.GET.get('page', '1'))
	except ValueError:
		page = 1
	try:
		letters = paginator.page(page)
	except (EmptyPage, InvalidPage):
		letters = paginator.page(paginator.num_pages)
	
	context['letters'] = letters

	return render_to_response('machiavelli/letter_box.html',
							context,
							context_instance=RequestContext(request))

@login_required
def new_letter(request, sender_id, receiver_id):
	player = get_object_or_404(Player, user=request.user, id=sender_id, eliminated=False)
	game = player.game
	context = base_context(request, game, player)
	receiver = get_object_or_404(Player, id=receiver_id, game=game, eliminated=False)
	## if the game is inactive, return 404 error
	if game.phase == 0:
		raise Http404
	if player.country.can_excommunicate and receiver.excommunicated:
		raise Http404
	if request.method == 'POST':
		letter_form = forms.LetterForm(player, receiver, data=request.POST)
		if letter_form.is_valid():
			letter = letter_form.save()
			if not player.excommunicated and receiver.excommunicated:
				player.excommunicate(year=receiver.excommunicated)
			return redirect('show-game', slug=game.slug)
		else:
			print letter_form.errors
	else:
		letter_form = forms.LetterForm(player, receiver)
		if not player.excommunicated and receiver.excommunicated:
			context['excom_notice'] = True
		if player.excommunicated and not receiver.excommunicated:
			raise Http404
	
	context.update({'form': letter_form,
					'sender': player,
					'receiver': receiver,
					})

	return render_to_response('machiavelli/letter_form.html',
							context,
							context_instance=RequestContext(request))

@login_required
def excommunicate(request, slug, player_id):
	game = get_object_or_404(Game, slug=slug)
	if game.phase == 0 or not game.configuration.excommunication:
		raise Http404
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
		raise Http404
	return redirect(game)

@login_required
def reset_excommunications(request, slug):
	game = get_object_or_404(Game, slug=slug)
	if game.phase == 0 or not game.configuration.excommunication:
		raise Http404
	player = get_object_or_404(Player, game=game, user=request.user)
	game.player_set.all().update(excommunicated=None)
	return redirect(game)

@cache_page(60 * 10)
def show_scenario(request, scenario_id):
	scenario = get_object_or_404(Scenario, id=scenario_id, enabled=True)

	countries = Country.objects.filter(home__scenario=scenario).distinct()
	autonomous = Setup.objects.filter(scenario=scenario, country__isnull=True)

	homes_dict = {}
	setups_dict = {}

	for c in countries:
		homes_dict[c] = c.home_set.filter(scenario=scenario)
		setups_dict[c] = c.setup_set.filter(scenario=scenario)

	return render_to_response('machiavelli/scenario_detail.html',
							{'scenario': scenario,
							'countries': countries,
							'homes': homes_dict,
							'setups': setups_dict,
							'autonomous': autonomous},
							context_instance=RequestContext(request))


@login_required
@cache_page(60 * 10)
def show_letter(request, letter_id):
	letters = Letter.objects.filter(Q(sender__user=request.user) | Q(receiver__user=request.user))
	try:
		letter = letters.get(id=letter_id)
	except:
		raise Http404
	if letter.receiver.user == request.user:
		letter.read = True
		letter.save()
	game = letter.sender.game
	player = Player.objects.get(user=request.user, game=game)
	context = base_context(request, game, player)
	context['letter'] = letter
	
	return render_to_response('machiavelli/letter_detail.html',
							context,
							context_instance=RequestContext(request))

#@login_required
@cache_page(60 * 10)
def hall_of_fame(request):
	profiles = CondottieriProfile.objects.all().order_by('-total_score')
	#users = User.objects.all().annotate(total_score=Sum('score__points')).order_by('-total_score')
	context = {'profiles': profiles}
	return render_to_response('machiavelli/hall_of_fame.html',
							context,
							context_instance=RequestContext(request))

@login_required
def low_karma_error(request):
	context = {
		'karma': request.user.get_profile().karma,
		'minimum': settings.KARMA_TO_JOIN,
	}
	return render_to_response('machiavelli/low_karma.html',
							context,
							context_instance=RequestContext(request))

@login_required
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
