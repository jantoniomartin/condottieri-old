import thread

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.generic.list_detail import object_list, object_detail
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.forms.formsets import formset_factory
from django.db.models import Q, Sum
#from django.forms.models import modelformset_factory
from django.views.decorators.cache import never_cache, cache_page
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings

from machiavelli.models import *
import machiavelli.utils as utils
import machiavelli.forms as forms
import machiavelli.graphics as graphics

#@login_required
def game_list(request):
	## check if the user has a Stats object associated.
	## this is probably not the best place to do this.
	##TODO: find a proper place for this code
	if request.user.is_authenticated():
		try:
			request.user.stats
		except:
			stats = Stats(user=request.user)
			stats.save()
	########
	active_games = Game.objects.exclude(slots=0, phase=PHINACTIVE)
	finished_games = Game.objects.filter(slots=0, phase=PHINACTIVE)
	if request.user.is_authenticated():
		other_games = active_games.exclude(player__user=request.user)
		your_games = active_games.filter(player__user=request.user)
		revolutions = []
		for r in Revolution.objects.filter(opposition__isnull=True):
			if r.government.game in other_games:
				revolutions.append(r)
	else:
		other_games = active_games
		your_games = Game.objects.none()
		revolutions = None
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
		#'phase_partial': "machiavelli/phase_%s.html" % game.phase,
		#'log': game.log_set.order_by('-id')[:10],
		'player': player,
		}
	log = game.baseevent_set.all()
	if player:
		context['phase_partial'] = "machiavelli/phase_%s.html" % game.phase
		context['inbox'] = player.received.order_by('-id')[:10]
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
		
	return context

@never_cache
#@login_required
def play_game(request, game_id=''):
	game = get_object_or_404(Game, pk=game_id)
	try:
		player = Player.objects.get(game=game, user=request.user)
	except:
		player = Player.objects.none()
	context = base_context(request, game, player)
	if game.slots == 0 and game.phase == PHINACTIVE:
		return redirect('game-results', game_id=game.id)
	if player:
		if game.slots == 0:
			game.check_time_limit()
		if not player.done:
			if game.phase == PHINACTIVE:
				pass
			elif game.phase == PHREINFORCE:
				print "Playing reinforcements phase"
				return play_reinforcements(request, game, player)
			elif game.phase == PHORDERS:
				print "Playing order writing phase"
				return play_orders(request, game, player)
			elif game.phase == PHRETREATS:
				print "Playing retreats"
				return play_retreats(request, game, player)
		else:
			context['done'] = True
			if game.phase == PHORDERS:
				orders = OrderEvent.objects.filter(game=game, year=game.year,
											season=game.season,
											phase=game.phase,
											country=player.country)
				context['orders'] = orders
	return render_to_response('machiavelli/show_game.html',
							context,
							context_instance=RequestContext(request))

def play_reinforcements(request, game, player):
	context = base_context(request, game, player)
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
					game.map_changed()
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
	else:
		## neither place or remove units
		#if request.method == 'POST':
		player.end_phase()
		return HttpResponseRedirect(request.path)
		#else:
		#	context['no_reinforcement'] = True
	return render_to_response('machiavelli/show_game.html',
							context,
							context_instance=RequestContext(request))

def play_orders(request, game, player):
	## receiving orders
	context = base_context(request, game, player)
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
	return render_to_response('machiavelli/show_game.html',
							context,
							context_instance=RequestContext(request))

def play_retreats(request, game, player):
	context = base_context(request, game, player)
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
	else:
		print "ending retreats phase"
		player.end_phase()
		return HttpResponseRedirect(request.path)
	return render_to_response('machiavelli/show_game.html',
							context,
							context_instance=RequestContext(request))

#@login_required
@cache_page(60 * 60) # cache 1 hour
def game_results(request, game_id):
	game = get_object_or_404(Game, pk=game_id)
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
def logs_by_game(request, game_id):
	game = get_object_or_404(Game, pk=game_id)
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
	karma = request.user.stats.karma
	if karma < settings.KARMA_TO_JOIN:
		return low_karma_error(request)
	##
	context = {'user': request.user,}
	if request.method == 'POST':
		form = forms.GameForm(request.user, data=request.POST)
		if form.is_valid():
			new_game = form.save(commit=False)
			new_game.slots = new_game.scenario.get_slots() - 1
			new_game.save()
			new_player = Player()
			new_player.user = request.user
			new_player.game = new_game
			new_player.save()
			## create the autonomous player
			#autonomous = Player(game=new_game, done=True)
			#autonomous.save()
			return redirect('game-list')
	else:
		form = forms.GameForm(request.user)
	context['scenarios'] = Scenario.objects.filter(enabled=True)
	context['form'] = form
	return render_to_response('machiavelli/game_form.html',
							context,
							context_instance=RequestContext(request))

@login_required
def join_game(request, game_id=''):
	g = get_object_or_404(Game, pk=game_id)
	karma = request.user.stats.karma
	if karma < settings.KARMA_TO_JOIN:
		return low_karma_error(request)
	if g.slots > 0:
		try:
			Player.objects.get(user=request.user, game=g)
		except:
			## the player is not in the game
			new_player = Player(user=request.user, game=g)
			new_player.save()
			g.player_joined()
	return redirect('game-list')

@login_required
def overthrow(request, revolution_id):
	revolution = get_object_or_404(Revolution, pk=revolution_id)
	try:
		Player.objects.get(user=request.user, game=revolution.government.game)
	except ObjectDoesNotExist:
		karma = request.user.stats.karma
		if karma < settings.KARMA_TO_JOIN:
			return low_karma_error(request)
		revolution.opposition = request.user
		revolution.save()
		return redirect('game-list')
	else:
		raise Http404

@never_cache
@login_required
def box_list(request, game_id='', box='inbox'):
	game = get_object_or_404(Game, pk=game_id)
	player = get_object_or_404(Player, game=game, user=request.user)
	extra_context = {
		'game': game,
		'player': player,
		'box': box,
	}

	if box == 'inbox':
		q = player.received.order_by('-id')
		template_name = 'machiavelli/letter_inbox.html'
	elif box == 'outbox':
		q = player.sent.order_by('-id')
		template_name = 'machiavelli/letter_outbox.html'
	else:
		q = Letter.objects.none()
	
	return object_list(
		request,
		queryset = q,
		template_name = template_name,
		template_object_name = 'letters',
		extra_context = extra_context
		)

@login_required
def new_letter(request, sender_id, receiver_id):
	player = get_object_or_404(Player, user=request.user, id=sender_id)
	game = player.game
	receiver = get_object_or_404(Player, id=receiver_id, game=game)
	## if the game is inactive, return 404 error
	if game.phase == 0:
		raise Http404
	if request.method == 'POST':
		letter_form = forms.LetterForm(player, receiver, data=request.POST)
		if letter_form.is_valid():
			letter = letter_form.save()
			return redirect('show-game', game_id=game.id)
		else:
			print letter_form.errors
	else:
		letter_form = forms.LetterForm(player, receiver)
	return render_to_response('machiavelli/letter_form.html',
							{'form': letter_form,
							'sender': player,
							'receiver': receiver,
							'player': player,
							'game': game,},
							context_instance=RequestContext(request))

@login_required
@cache_page(60 * 10)
def show_letter(request, letter_id):
	letters = Letter.objects.filter(Q(sender__user=request.user) | Q(receiver__user=request.user))
	try:
		letter = letters.get(id=letter_id)
	except:
		raise Http404
	else:
		letter.read = True
		letter.save()
	game = letter.sender.game
	player = Player.objects.get(user=request.user, game=game)
	extra_context = {
		'game': game,
		'player': player,
	}
	return object_detail(
		request,
		queryset = letters,
		object_id = letter_id,
		template_name = 'machiavelli/letter_detail.html',
		template_object_name = 'letter',
		extra_context = extra_context
	)

#@login_required
@cache_page(60 * 10)
def hall_of_fame(request):
	users = User.objects.all().annotate(total_score=Sum('score__points')).order_by('-total_score')
	context = {'users': users}
	return render_to_response('machiavelli/hall_of_fame.html',
							context,
							context_instance=RequestContext(request))

@login_required
def low_karma_error(request):
	context = {
		'karma': request.user.stats.karma,
		'minimum': settings.KARMA_TO_JOIN,
	}
	return render_to_response('machiavelli/low_karma.html',
							context,
							context_instance=RequestContext(request))

