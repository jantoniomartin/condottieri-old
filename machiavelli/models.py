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

""" Class definitions for machiavelli django application

Defines the core classes of the machiavelli game.
"""

## stdlib
import random
import thread
from datetime import datetime, timedelta

## django
from django.db import models
from django.db.models import permalink, Q, F, Count, Sum
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.cache import cache
from django.contrib.auth.models import User
import django.forms as forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.template.defaultfilters import capfirst, truncatewords

if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None

if "jogging" in settings.INSTALLED_APPS:
	from jogging import logging
else:
	logging = None

if "condottieri_messages" in settings.INSTALLED_APPS:
	import condottieri_messages as condottieri_messages 
else:
	condottieri_messages = None

## machiavelli
from machiavelli.fields import AutoTranslateField
from machiavelli.graphics import make_map
from machiavelli.logging import save_snapshot
import machiavelli.dice as dice
import machiavelli.disasters as disasters
import machiavelli.finances as finances
import machiavelli.exceptions as exceptions

## condottieri_profiles
from condottieri_profiles.models import CondottieriProfile

## condottieri_events
if "condottieri_events" in settings.INSTALLED_APPS:
	import machiavelli.signals as signals
else:
	signals = None

try:
	settings.TWITTER_USER
except:
	twitter_api = None
else:
	import twitter
	twitter_api = twitter.Api(username=settings.TWITTER_USER,
							  password=settings.TWITTER_PASSWORD)

UNIT_TYPES = (('A', _('Army')),
              ('F', _('Fleet')),
              ('G', _('Garrison'))
			  )

SEASONS = ((1, _('Spring')),
           (2, _('Summer')),
           (3, _('Fall')),
           )

PHINACTIVE=0
PHREINFORCE=1
PHORDERS=2
PHRETREATS=3

GAME_PHASES = ((PHINACTIVE, _('Inactive game')),
	  (PHREINFORCE, _('Military adjustments')),
	  (PHORDERS, _('Order writing')),
	  (PHRETREATS, _('Retreats')),
	  )

ORDER_CODES = (('H', _('Hold')),
			   ('B', _('Besiege')),
			   ('-', _('Advance')),
			   ('=', _('Conversion')),
			   ('C', _('Convoy')),
			   ('S', _('Support'))
				)
ORDER_SUBCODES = (
				('H', _('Hold')),
				('-', _('Advance')),
				('=', _('Conversion'))
)

## time limit in seconds for a game phase
FAST_LIMITS = (15*60, )

TIME_LIMITS = (
			#(5*24*60*60, _('5 days')),
			#(4*24*60*60, _('4 days')),
			#(3*24*60*60, _('3 days')),
			(2*24*60*60, _('2 days')),
			(24*60*60, _('1 day')),
			(12*60*60, _('1/2 day')),
			(15*60, _('15 min')),
)

## SCORES
## points assigned to the first, second and third players
SCORES=[20, 10, 5]

KARMA_MINIMUM = settings.KARMA_MINIMUM
KARMA_DEFAULT = settings.KARMA_DEFAULT
KARMA_MAXIMUM = settings.KARMA_MAXIMUM
BONUS_TIME = settings.BONUS_TIME

class Invasion(object):
	""" This class is used in conflicts resolution for conditioned invasions.
	Invasion objects are not persistent (i.e. not stored in the database).
	"""

	def __init__(self, unit, area, conv=''):
		assert isinstance(unit, Unit), u"%s is not a Unit" % unit
		assert isinstance(area, GameArea), u"%s is not a GameArea" % area
		assert conv in ['', 'A', 'F'], u"%s is not a valid conversion" % conv
		self.unit = unit
		self.area = area
		self.conversion = conv

class Scenario(models.Model):
	""" This class defines a Machiavelli scenario basic data. """

	name = models.CharField(max_length=16, unique=True)
	title = AutoTranslateField(max_length=128)
	start_year = models.PositiveIntegerField()
	## this field is added to improve the performance of some queries
	number_of_players = models.PositiveIntegerField(default=0)
	cities_to_win = models.PositiveIntegerField(default=15)
	enabled = models.BooleanField(default=False) # this allows me to create the new setups in the admin

	def get_slots(self):
		#slots = len(self.setup_set.values('country').distinct()) - 1
		return self.number_of_players

	def __unicode__(self):
		return self.title

	def get_absolute_url(self):
		return "scenario/%s" % self.id

	def get_countries(self):
		return Country.objects.filter(home__scenario=self).distinct()

if twitter_api and settings.TWEET_NEW_SCENARIO:
	def tweet_new_scenario(sender, instance, created, **kw):
		if twitter_api and isinstance(instance, Scenario):
			if created == True:
				message = "A new scenario has been created: %s" % instance.title
				twitter_api.PostUpdate(message)

	models.signals.post_save.connect(tweet_new_scenario, sender=Scenario)

class Country(models.Model):
	""" This class defines a Machiavelly country. """

	name = AutoTranslateField(max_length=20, unique=True)
	css_class = models.CharField(max_length=20, unique=True)
	can_excommunicate = models.BooleanField(default=False)
	static_name = models.CharField(max_length=20, default="")

	def __unicode__(self):
		return self.name

class Area(models.Model):
	""" his class describes **only** the area features in the board. The game is
actually played in GameArea objects.
	"""

	name = AutoTranslateField(max_length=25, unique=True)
	code = models.CharField(max_length=5 ,unique=True)
	is_sea = models.BooleanField(default=False)
	is_coast = models.BooleanField(default=False)
	has_city = models.BooleanField(default=False)
	is_fortified = models.BooleanField(default=False)
	has_port = models.BooleanField(default=False)
	borders = models.ManyToManyField("self", editable=False)
	## control_income is the number of ducats that the area gives to the player
	## that controls it, including the city (seas give 0)
	control_income = models.PositiveIntegerField(null=False, default=0)
	## garrison_income is the number of ducats given by an unbesieged
	## garrison in the area's city, if any (no fortified city, 0)
	garrison_income = models.PositiveIntegerField(null=False, default=0)

	def is_adjacent(self, area, fleet=False):
		""" Two areas can be adjacent through land, but not through a coast. 
		
		The list ``only_armies`` shows the areas that are adjacent but their
		coasts are not, so a Fleet can move between them.
		"""

		only_armies = [
			('AVI', 'PRO'),
			('PISA', 'SIE'),
			('CAP', 'AQU'),
			('NAP', 'AQU'),
			('SAL', 'AQU'),
			('SAL', 'BARI'),
			('HER', 'ALB'),
			('BOL', 'MOD'),
			('BOL', 'LUC'),
			('CAR', 'CRO'),
		]
		if fleet:
			if (self.code, area.code) in only_armies or (area.code, self.code) in only_armies:
				return False
		return area in self.borders.all()

	def accepts_type(self, type):
		""" Returns True if an given type of Unit can be in the Area. """

		assert type in ('A', 'F', 'G'), 'Wrong unit type'
		if type=='A':
			if self.is_sea or self.code=='VEN':
				return False
		elif type=='F':
			if not self.has_port:
				return False
		else:
			if not self.is_fortified:
				return False
		return True

	def __unicode__(self):
		return "%(code)s - %(name)s" % {'name': self.name, 'code': self.code}
	
	class Meta:
		ordering = ('code',)

class DisabledArea(models.Model):
	""" A DisabledArea is an Area that is not used in a given Scenario. """
	scenario = models.ForeignKey(Scenario)
	area = models.ForeignKey(Area)

	def __unicode__(self):
		return "%(area)s disabled in %(scenario)s" % {'area': self.area,
													'scenario': self.scenario}
	
	class Meta:
		unique_together = (('scenario', 'area'),) 

class Home(models.Model):
	""" This class defines which Country controls each Area in a given Scenario,
	at the beginning of a game.
	
	Note that, in some special cases, a province controlled by a country does
	not belong to the **home country** of this country. The ``is_home``
	attribute controls that.
	"""

	scenario = models.ForeignKey(Scenario)
	country = models.ForeignKey(Country)
	area = models.ForeignKey(Area)
	is_home = models.BooleanField(default=True)

	def __unicode__(self):
		return "%s" % self.area.name

	class Meta:
		unique_together = (("scenario", "country", "area"),)

class Setup(models.Model):
	""" This class defines the initial setup of a unit in a given Scenario. """

	scenario = models.ForeignKey(Scenario)
	country = models.ForeignKey(Country, blank=True, null=True)
	area = models.ForeignKey(Area)
	unit_type = models.CharField(max_length=1, choices=UNIT_TYPES)
    
	def __unicode__(self):
		return "%s in %s" % (self.get_unit_type_display(), self.area.name)

	class Meta:
		unique_together = (("scenario", "area", "unit_type"),)

class Treasury(models.Model):
	""" This class represents the initial amount of ducats that a Country starts
	each Scenario with """
	
	scenario = models.ForeignKey(Scenario)
	country = models.ForeignKey(Country)
	ducats = models.PositiveIntegerField(default=0)
	double = models.BooleanField(default=False)

	def __unicode__(self):
		return "%s starts %s with %s ducats" % (self.country, self.scenario, self.ducats)

	class Meta:
		unique_together = (("scenario", "country"),)


class CityIncome(models.Model):
	""" This class represents a City that generates an income in a given
	Scenario"""
	
	city = models.ForeignKey(Area)
	scenario = models.ForeignKey(Scenario)

	def __unicode__(self):
		return "%s" % self.city.name

	class Meta:
		unique_together = (("city", "scenario"),)


class Game(models.Model):
	""" This is the main class of the machiavelli application. It includes all the
	logic to control the flow of the game, and to resolve conflicts.

	The attributes year, season and field are null when the game is first created
	and will be populated when the game is started, from the scenario data.
	"""

	slug = models.SlugField(max_length=20, unique=True)
	year = models.PositiveIntegerField(blank=True, null=True)
	season = models.PositiveIntegerField(blank=True, null=True,
					     choices=SEASONS)
	phase = models.PositiveIntegerField(blank=True, null=True,
					    choices=GAME_PHASES, default=0)
	slots = models.SmallIntegerField(null=False, default=0)
	scenario = models.ForeignKey(Scenario)
	created_by = models.ForeignKey(User, editable=False)
	## whether the player of each country is visible
	visible = models.BooleanField(default=0)
	map_outdated = models.BooleanField(default=0)
	time_limit = models.PositiveIntegerField(choices=TIME_LIMITS)
	## the time and date of the last phase change
	last_phase_change = models.DateTimeField(blank=True, null=True)
	created = models.DateTimeField(blank=True, null=True, auto_now_add=True)
	started = models.DateTimeField(blank=True, null=True)
	finished = models.DateTimeField(blank=True, null=True)
	cities_to_win = models.PositiveIntegerField(default=15)
	fast = models.BooleanField(default=0)

	def save(self, *args, **kwargs):
		if not self.pk:
			self.fast = self.time_limit in FAST_LIMITS
		super(Game, self).save(*args, **kwargs)

	##------------------------
	## representation methods
	##------------------------
	def __unicode__(self):
		return "%d" % (self.pk)

	def get_map_url(self):
		return "map-%s.jpg" % self.id
	
	def get_absolute_url(self):
		return ('show-game', None, {'slug': self.slug})
	get_absolute_url = models.permalink(get_absolute_url)
	
	def player_list_ordered_by_cities(self):
		key = "game-%s_player-list" % self.pk
		result_list = cache.get(key)
		if result_list is None:
			from django.db import connection
			cursor = connection.cursor()
			cursor.execute("SELECT machiavelli_player.*, COUNT(machiavelli_gamearea.id) \
			AS cities \
			FROM machiavelli_player \
			LEFT JOIN (machiavelli_gamearea \
			INNER JOIN machiavelli_area \
			ON machiavelli_gamearea.board_area_id=machiavelli_area.id) \
			ON machiavelli_gamearea.player_id=machiavelli_player.id \
			WHERE (machiavelli_player.game_id=%s AND machiavelli_player.country_id \
			AND (machiavelli_area.has_city=1 OR machiavelli_gamearea.id IS NULL)) \
			GROUP BY machiavelli_player.id \
			ORDER BY cities DESC, machiavelli_player.id;" % self.id)
			result_list = []
			for row in cursor.fetchall():
				result_list.append(Player.objects.get(id=row[0]))
			cache.set(key, result_list)
		return result_list

	def highest_score(self):
		""" Returns the Score with the highest points value. """

		if self.slots > 0 or self.phase != PHINACTIVE:
			return Score.objects.none()
		scores = self.score_set.all().order_by('-points')
		return scores[0]

	def get_all_units(self):
		""" Returns a queryset with all the units in the board. """
		key = "game-%s_all-units" % self.pk
		all_units = cache.get(key)
		if all_units is None:
			all_units = Unit.objects.select_related().filter(player__game=self).order_by('area__board_area__name')
			cache.set(key, all_units)
		return all_units

	def get_all_gameareas(self):
		""" Returns a queryset with all the game areas in the board. """
		key = "game-%s_all-areas" % self.pk
		all_areas = cache.get(key)
		if all_areas is None:
			all_areas = self.gamearea_set.select_related().order_by('board_area__code')
			cache.set(key, all_areas)
		return all_areas

	##------------------------
	## map methods
	##------------------------
	
	def make_map(self):
		make_map(self)
		#thread.start_new_thread(make_map, (self,))
		return True

	def map_changed(self):
		if self.map_outdated == False:
			self.map_outdated = True
			self.save()
	
	def map_saved(self):
		if self.map_outdated == True:
			self.map_outdated = False
			self.save()

	##------------------------
	## game starting methods
	##------------------------

	def player_joined(self):
		self.slots -= 1
		#self.map_outdated = True
		if self.slots == 0:
			#the game has all its players and should start
			if logging:
				logging.info("Starting game %s" % self.id)
			self.year = self.scenario.start_year
			self.season = 1
			self.phase = PHORDERS
			self.create_game_board()
			self.shuffle_countries()
			self.copy_country_data()
			self.home_control_markers()
			self.place_initial_units()
			if self.configuration.finances:
				self.assign_initial_income()
			if self.configuration.assassinations:
				self.create_assassins()
			#self.map_outdated = True
			self.make_map()
			self.started = datetime.now()
			self.last_phase_change = datetime.now()
			self.notify_players("game_started", {"game": self})
		self.save()
		#if self.map_outdated == True:
		#	self.make_map()
	
	def shuffle_countries(self):
		""" Assign a Country of the Scenario to each Player, randomly. """

		countries_dict = self.scenario.setup_set.values('country').distinct()
		countries = []
		for c in countries_dict:
			for v in c.values():
				if v:
					countries.append(v)
		## the number of players and countries should be the same
		assert len(countries) == len(self.player_set.filter(user__isnull=False)), "Number of players should be the same as number of countries"
		## a list of tuples will be returned
		assignment = []
		## shuffle the list of countries
		random.shuffle(countries)
		for player in self.player_set.filter(user__isnull=False):
			assignment.append((player, countries.pop()))
		for t in assignment:
			t[0].country = Country.objects.get(id=t[1])
			t[0].save()

	def copy_country_data(self):
		""" Copies to the player objects some properties that will never change during the game.
		This way, I hope to save some hits to the database """
		excom = self.configuration.excommunication
		finances = self.configuration.finances

		for p in self.player_set.filter(user__isnull=False):
			p.static_name = p.country.static_name
			if excom:
				p.may_excommunicate = p.country.can_excommunicate
			if finances:
				t = Treasury.objects.get(scenario=self.scenario, country=p.country)
				p.double_income = t.double
			p.save()

	def get_disabled_areas(self):
		""" Returns the disabled Areas in the game scenario """
		return Area.objects.filter(disabledarea__scenario=self.scenario)

	def create_game_board(self):
		""" Creates the GameAreas for the Game.	"""
		disabled_ids = Area.objects.filter(disabledarea__scenario=self.scenario).values_list('id', flat=True)
		for a in Area.objects.all():
			if not a.id in disabled_ids:
				ga = GameArea(game=self, board_area=a)
				ga.save()

	def get_autonomous_setups(self):
		return Setup.objects.filter(scenario=self.scenario,
				country__isnull=True).select_related()
	
	def place_initial_garrisons(self):
		""" Creates the Autonomous Player, and places the autonomous garrisons at the
		start of the game.
		"""

		## create the autonomous player
		autonomous = Player(game=self, done=True)
		autonomous.save()
		for s in self.get_autonomous_setups():
			try:
				a = GameArea.objects.get(game=self, board_area=s.area)
			except:
				print "Error 1: Area not found!"
			else:	
				if s.unit_type:
					new_unit = Unit(type='G', area=a, player=autonomous)
					new_unit.save()

	def home_control_markers(self):
		for p in self.player_set.filter(user__isnull=False):
			p.home_control_markers()

	def place_initial_units(self):
		for p in self.player_set.filter(user__isnull=False):
			p.place_initial_units()
		self.place_initial_garrisons()

	def assign_initial_income(self):
		for p in self.player_set.filter(user__isnull=False):
			t = Treasury.objects.get(scenario=self.scenario, country=p.country)
			p.ducats = t.ducats
			p.save()

	def create_assassins(self):
		""" Assign each player an assassination counter for each of the other players """
		for p in self.player_set.filter(user__isnull=False):
			for q in self.player_set.filter(user__isnull=False):
				if q == p:
					continue
				assassin = Assassin()
				assassin.owner = p
				assassin.target = q.country
				assassin.save()

	##--------------------------
	## time controlling methods
	##--------------------------

	def clear_phase_cache(self):
		cache_keys = [
			"game-%s_player_list" % self.pk,
			"game-%s_all-units" % self.pk,
			"game-%s_all-areas" % self.pk,
		]
		for k in cache_keys:
			cache.delete(k)

	def get_highest_karma(self):
		""" Returns the karma of the non-finished player with the highest value.
			
			Returns 0 if all the players have finished.
		"""

		players = CondottieriProfile.objects.filter(user__player__game=self,
								user__player__done=False).order_by('-karma')
		if len(players) > 0:
			return float(players[0].karma)
		return 0


	def next_phase_change(self):
		""" Returns the Time of the next compulsory phase change. """
		if self.phase == PHINACTIVE :
			return False	
		if self.fast:
			## do not use karma
			time_limit = self.time_limit
		else:
			## get the player with the highest karma, and not done
			highest = self.get_highest_karma()
			if highest > 100:
				if self.phase == PHORDERS:
					k = 1 + (highest - 100) / 200
				else:
					k = 1
			else:
				k = highest / 100
			time_limit = self.time_limit * k
		
		duration = timedelta(0, time_limit)

		return self.last_phase_change + duration
	

	def force_phase_change(self):
		""" When the time limit is reached and one or more of the players are not
		done, a phase change is forced.
		"""

		for p in self.player_set.all():
			if p.done:
				continue
			else:
				if self.phase == PHREINFORCE:
					if self.configuration.finances:
						units = Unit.objects.filter(player=p).order_by('id')
						ducats = p.ducats
						payable = ducats / 3
						cost = 0
						if payable > 0:
							for u in units[:payable]:
								u.paid = True
								u.save()
								cost += 3
						p.ducats = ducats - cost
						p.save()
					else:
						units = Unit.objects.filter(player=p).order_by('-id')
						reinforce = p.units_to_place()
						if reinforce < 0:
							## delete the newest units
							for u in units[:-reinforce]:
								u.delete()
				elif self.phase == PHORDERS:
					pass
				elif self.phase == PHRETREATS:
					## disband the units that should retreat
					Unit.objects.filter(player=p).exclude(must_retreat__exact='').delete()
				p.end_phase(forced=True)
		
	def time_is_exceeded(self):
		""" Checks if the time limit has been reached. If yes, return True """

		if not self.phase == PHINACTIVE:
			limit = self.next_phase_change()
			to_limit = limit - datetime.now()
			return to_limit <= timedelta(0, 0)
			#self.force_phase_change()
	
	def check_finished_phase(self):
		""" This method is to be called by a management script, called by cron.
		It checks if all the players are done, then process the phase.
		If at least a player is not done, check the time limit
		"""
		players = self.player_set.all()
		msg = u"Checking phase change in game %s\n" % self.pk
		if self.time_is_exceeded():
			msg += u"Time exceeded.\n"
			self.force_phase_change()
		for p in players:
			if not p.done:
				msg += u"At least a player is not done.\n"
				return False
		msg += u"All players done.\n"
		if logging:
			logging.info(msg)
		self.all_players_done()
		self.clear_phase_cache()
		## If I don't reload players, p.new_phase overwrite the changes made by
		## self.assign_incomes()
		## TODO: optimize this
		players = self.player_set.all()
		for p in players:
			p.new_phase()

	
	def check_bonus_time(self):
		""" Returns true if, when the function is called, the first BONUS_TIME% of the
		duration has not been reached.
		"""

		duration = timedelta(0, self.time_limit * BONUS_TIME)
		limit = self.last_phase_change + duration
		to_limit = limit - datetime.now()
		if to_limit >= timedelta(0, 0):
			return True
		else:
			return False

	def get_bonus_deadline(self):
		""" Returns the latest time when karma is bonified """
		duration = timedelta(0, self.time_limit * BONUS_TIME)
		return self.last_phase_change + duration
	
	def _next_season(self):
		## take a snapshot of the units layout
		#thread.start_new_thread(save_snapshot, (self,))
		save_snapshot(self)
		if self.season == 3:
			self.season = 1
			self.year += 1
		else:
			self.season += 1
		## delete all retreats and standoffs
		Unit.objects.filter(player__game=self).update(must_retreat='')
		GameArea.objects.filter(game=self).update(standoff=False)

	def all_players_done(self):
		end_season = False
		if self.phase == PHINACTIVE:
			return
		elif self.phase == PHREINFORCE:
			self.adjust_units()
			next_phase = PHORDERS
		elif self.phase == PHORDERS:
			if self.configuration.lenders:
				self.check_loans()
			if self.configuration.finances:
				self.process_expenses()
			if self.configuration.assassinations:
				self.process_assassinations()
			if self.configuration.assassinations or self.configuration.lenders:
				## if a player is assassinated, all his orders become 'H'
				for p in self.player_set.filter(assassinated=True):
					p.cancel_orders()
					for area in p.gamearea_set.exclude(board_area__is_sea=True):
						area.check_assassination_rebellion()
			self.process_orders()
			Order.objects.filter(unit__player__game=self).delete()
			retreats_count = Unit.objects.filter(player__game=self).exclude(must_retreat__exact='').count()
			if retreats_count > 0:
				next_phase = PHRETREATS
			else:
				end_season = True
		elif self.phase == PHRETREATS:
			self.process_retreats()
			end_season = True
		if end_season:
			if self.season == 1:
				## delete units in famine areas
				if self.configuration.famine:
					famine_units = Unit.objects.filter(player__game=self, area__famine=True)
					for f in famine_units:
						f.delete()
					## reset famine markers
					self.gamearea_set.all().update(famine=False)
					## check plagues
					self.kill_plague_units()
			elif self.season == 3:
				## if conquering is enabled, check if any users are eliminated
				if self.configuration.conquering:
					for p in self.player_set.filter(eliminated=False,
													user__isnull=False):
						if p.check_eliminated():
							p.eliminate()
				self.update_controls()
				## if conquering is enabled, check conquerings
				if self.configuration.conquering:
					self.check_conquerings()
				if self.check_winner() == True:
					self.make_map()
					self.assign_scores()
					self.game_over()
					return
				## if famine enabled, place famine markers
				if self.configuration.famine:
					self.mark_famine_areas()
				## if finances are enabled, assign incomes
				if self.configuration.finances:
					try:
						self.assign_incomes()
					except Exception, e:
						print "Error assigning incomes in game %s:\n" % self.id
						print e
			## reset assassinations
			self.player_set.all().update(assassinated=False)
			self._next_season()
			if self.season == 1:
				## if there are not finances all units are paid
				if not self.configuration.finances:
					next_phase = PHORDERS
					Unit.objects.filter(player__game=self).update(paid=True)
					for p in self.player_set.all():
						if p.units_to_place() != 0:
							next_phase = PHREINFORCE
							break
				else:
					## if playing with finances, reinforcement phase must be always played
					next_phase = PHREINFORCE
			else:
				next_phase = PHORDERS
		self.phase = next_phase
		self.last_phase_change = datetime.now()
		#self.map_changed()
		self.save()
		self.make_map()
		self.notify_players("new_phase", {"game": self})
    
	def adjust_units(self):
		""" Places new units and disbands the ones that are not paid """
		to_disband = Unit.objects.filter(player__game=self, paid=False)
		for u in to_disband:
			u.delete()
		to_place = Unit.objects.filter(player__game=self, placed=False)
		for u in to_place:
			u.place()
		## mark as unpaid all non-autonomous units
		Unit.objects.filter(player__game=self).exclude(player__user__isnull=True).update(paid=False)

	## deprecated because of check_finished_phase
	#def check_next_phase(self):
	#	""" When a player ends its phase, send a signal to the game. This function
	#	checks if all the players have finished.
	#	"""
	#
	#	for p in self.player_set.all():
	#		if not p.done:
	#			return False
	#	self.all_players_done()
	#	for p in self.player_set.all():
	#		p.new_phase()

	##------------------------
	## optional rules methods
	##------------------------
	def check_conquerings(self):
		if not self.configuration.conquering:
			return
		## a player can only be conquered if he is eliminated
		for p in self.player_set.filter(eliminated=True):
			## get the players that control part of this player's home country
			controllers = self.player_set.filter(gamearea__board_area__home__country=p.country,
									gamearea__board_area__home__scenario=self.scenario,
									gamearea__board_area__home__is_home=True).distinct()
			if len(controllers) == 1:
				 ## all the areas in home country belong to the same player
				 if p != controllers[0] and p.conqueror != controllers[0]:
				 	## controllers[0] conquers p
					p.set_conqueror(controllers[0])

	def mark_famine_areas(self):
		if not self.configuration.famine:
			return
		codes = disasters.get_famine()
		famine_areas = GameArea.objects.filter(game=self, board_area__code__in=codes)
		for f in famine_areas:
			f.famine=True
			f.save()
			signals.famine_marker_placed.send(sender=f)
	
	def kill_plague_units(self):
		if not self.configuration.plague:
			return
		codes = disasters.get_plague()
		plague_areas = GameArea.objects.filter(game=self, board_area__code__in=codes)
		for p in plague_areas:
			signals.plague_placed.send(sender=p)
			for u in p.unit_set.all():
				u.delete()

	def assign_incomes(self):
		""" Gets each player's income and add it to the player's treasury """
		## get the column for variable income
		die = dice.roll_1d6()
		if logging:
			msg = "Varible income: Got a %s in game %s" % (die, self)
			logging.info(msg)
		## get a list of the ids of the major cities that generate income
		majors = CityIncome.objects.filter(scenario=self.scenario)
		majors_ids = majors.values_list('city', flat=True)
		##
		players = self.player_set.filter(user__isnull=False, eliminated=False)
		for p in players:
			i = p.get_income(die, majors_ids)
			if i > 0:
				p.add_ducats(i)

	def check_loans(self):
		""" Check if any loans have exceeded their terms. If so, apply the
		penalties. """
		loans = Loan.objects.filter(player__game=self)
		for loan in loans:
			if self.year >= loan.year and self.season >= loan.season:
				## the loan has exceeded its term
				if logging:
					msg = "%s defaulted" % loan.player
					logging.info(msg)
				loan.player.defaulted = True
				loan.player.save()
				loan.player.assassinate()
				loan.delete()
	
	def process_expenses(self):
		## First, process famine reliefs
		for e in Expense.objects.filter(player__game=self, type=0):
			e.area.famine = False
			e.area.save()
		## then, delete the rebellions
		for e in Expense.objects.filter(player__game=self, type=1):
			Rebellion.objects.filter(area=e.area).delete()
		## then, place new rebellions
		for e in Expense.objects.filter(player__game=self, type__in=(2,3)):
			try:
				rebellion = Rebellion(area=e.area)
				rebellion.save()
			except:
				continue
		## then, delete bribes that are countered
		expenses = Expense.objects.filter(player__game=self)
		for e in expenses:
			if e.is_bribe():
				## get the sum of counter-bribes
				cb = Expense.objects.filter(player__game=self, type=4, unit=e.unit).aggregate(Sum('ducats'))
				if not cb['ducats__sum']:
					cb['ducats__sum'] = 0
				total_cost = get_expense_cost(e.type, e.unit) + cb['ducats__sum']
				if total_cost > e.ducats:
					e.delete()
		## then, resolve the bribes for each bribed unit
		bribed_ids = Expense.objects.filter(unit__player__game=self, type__in=(5,6,7,8,9)).values_list('unit', flat=True).distinct()
		chosen = []
		## TODO: if two bribes have the same value, decide randomly between them
		for i in bribed_ids:
			bribes = Expense.objects.filter(type__in=(5,6,7,8,9), unit__id=i).order_by('-ducats')
			chosen.append(bribes[0])
		## all bribes in 'chosen' are successful, and executed
		for c in chosen:
			if c.type in (5, 8): #disband unit
				c.unit.delete()
			elif c.type in (6, 9): #buy unit
				c.unit.change_player(c.player)
			elif c.type == 7: #to autonomous
				c.unit.to_autonomous()
		## finally, delete all the expenses
		Expense.objects.filter(player__game=self).delete()

	def get_rebellions(self):
		""" Returns a queryset with all the rebellions in this game """
		return Rebellion.objects.filter(area__game=self)

	def process_assassinations(self):
		""" Resolves all the assassination attempts """
		attempts = Assassination.objects.filter(killer__game=self)
		victims = []
		msg = u"Processing assassinations in game %s:\n" % self
		for a in attempts:
			msg += u"\n%s spends %s ducats to kill %s\n" % (a.killer, a.ducats, a.target)
			if a.target in victims:
				msg += u"%s already killed\n" % a.target
				continue
			dice_rolled = int(a.ducats / 12)
			msg += u"%s dice will be rolled\n" % dice_rolled
			if dice.check_one_six(dice_rolled):
				msg += u"Attempt is successful\n"
				## attempt is successful
				a.target.assassinate()
				victims.append(a.target)
			else:
				msg += u"Attempt fails\n"
		attempts.delete()
		if logging:
			logging.info(msg)


	##------------------------
	## turn processing methods
	##------------------------

	def get_conflict_areas(self):
		""" Returns the orders that could result in a possible conflict these are the
		advancing units and the units that try to convert into A or F.
		"""

		conflict_orders = Order.objects.filter(unit__player__game=self, code__in=['-', '=']).exclude(type__exact='G')
		conflict_areas = []
		for o in conflict_orders:
			if o.code == '-':
				if o.unit.area.board_area.is_adjacent(o.destination.board_area, fleet=(o.unit.type=='F')) or \
					o.find_convoy_line():
						area = o.destination
				else:
					continue
			else:
				## unit trying to convert into A or F
				area = o.unit.area
			conflict_areas.append(area)
		return conflict_areas

	def filter_supports(self):
		""" Checks which Units with support orders are being attacked and delete their
		orders.
		"""

		info = u"Step 2: Cancel supports from units under attack.\n"
		support_orders = Order.objects.filter(unit__player__game=self, code__exact='S')
		for s in support_orders:
			info += u"Checking order %s.\n" % s
			if s.unit.type != 'G' and s.unit.area in self.get_conflict_areas():
				attacks = Order.objects.filter(~Q(unit__player=s.unit.player) &
												((Q(code__exact='-') & Q(destination=s.unit.area)) |
												(Q(code__exact='=') & Q(unit__area=s.unit.area) &
												Q(unit__type__exact='G'))))
				if len(attacks) > 0:
					info += u"Supporting unit is being attacked.\n"
					for a in attacks:
						if (s.subcode == '-' and s.subdestination == a.unit.area) or \
						(s.subcode == '=' and s.subtype in ['A','F'] and s.subunit.area == a.unit.area):
							info += u"Support is not broken.\n"
							continue
						else:
							info += u"Attack from %s breaks support.\n" % a.unit
							if signals:
								signals.support_broken.send(sender=s.unit)
							else:
								self.log_event(UnitEvent, type=s.unit.type, area=s.unit.area.board_area, message=0)
							s.delete()
							break
		return info

	def filter_convoys(self):
		""" Checks which Units with C orders are being attacked. Checks if they
		are going to be defeated, and if so, delete the C order. However, it
		doesn't resolve the conflict
		"""

		info = u"Step 3: Cancel convoys by fleets that will be dislodged.\n"
		## find units attacking fleets
		sea_attackers = Unit.objects.filter(Q(player__game=self),
											(Q(order__code__exact='-') &
											Q(order__destination__board_area__is_sea=True)) |
											(Q(order__code__exact='=') &
											Q(area__board_area__code__exact='VEN') &
											Q(type__exact='G')))
		for s in sea_attackers:
			order = s.get_order()
			try:
				## find the defender
				if order.code == '-':
					defender = Unit.objects.get(player__game=self,
											area=order.destination,
											type__exact='F',
											order__code__exact='C')
				elif order.code == '=' and s.area.board_area.code == 'VEN':
					defender = Unit.objects.get(player__game=self,
												area=s.area,
												type__exact='F',
												order__code__exact='C')
			except:
				## no attacked convoying fleet is found 
				continue
			else:
				info += u"Convoying %s is being attacked by %s.\n" % (defender, s)
				a_strength = Unit.objects.get_with_strength(self, id=s.id).strength
				d_strength = Unit.objects.get_with_strength(self, id=defender.id).strength
				if a_strength > d_strength:
					d_order = defender.get_order()
					if d_order:
						info += u"%s can't convoy.\n" % defender
						defender.delete_order()
					else:
						continue
		return info
	
	def filter_unreachable_attacks(self):
		""" Delete the orders of units trying to go to non-adjacent areas and not
		having a convoy line.
		"""

		info = u"Step 4: Cancel attacks to unreachable areas.\n"
		attackers = Order.objects.filter(unit__player__game=self, code__exact='-')
		for o in attackers:
			is_fleet = (o.unit.type == 'F')
			if not o.unit.area.board_area.is_adjacent(o.destination.board_area, is_fleet):
				if is_fleet:
					info += u"Impossible attack: %s.\n" % o
					o.delete()
				else:
					if not o.find_convoy_line():
						info += u"Impossible attack: %s.\n" % o
						o.delete()
		return info
	
	def resolve_auto_garrisons(self):
		""" Units with '= G' orders in areas without a garrison, convert into garrison.
		"""

		info = u"Step 1: Garrisoning units.\n"
		garrisoning = Unit.objects.filter(player__game=self,
									order__code__exact='=',
									order__type__exact='G')
		for g in garrisoning:
			info += u"%s tries to convert into garrison.\n" % g
			try:
				defender = Unit.objects.get(player__game=self,
										type__exact='G',
										area=g.area)
			except:
				info += u"Success!\n"
				g.convert('G')
				g.delete_order()
			else:
				info += u"Fail: there is a garrison in the city.\n"
		return info

	def resolve_conflicts(self):
		""" Conflict: When two or more units want to occupy the same area.
		
		This method takes all the units and decides which unit occupies each conflict
		area and which units must retreat.
		"""

		## units sorted (reverse) by a temporary strength attribute
		## strength = 0 means unit without supports
		info = u"Step 5: Process conflicts.\n"
		units = Unit.objects.list_with_strength(self)
		conditioned_invasions = []
		conditioned_origins = []
		finances = self.configuration.finances
		holding = []
		## iterate all the units
		for u in units:
			## discard all the units with H, S, B, C or no orders
			## they will not move
			u_order = u.get_order()
			if not u_order:
				info += u"%s has no orders.\n" % u
				continue
			else:
				info += u"%s was ordered: %s.\n" % (u, u_order)
				if finances and u_order.code == 'H':
					## the unit counts for removing a rebellion
					holding.append(u)
				if u_order.code in ['H', 'S', 'B', 'C']:
					continue
			##################
			s = u.strength
			info += u"Supported by = %s.\n" % s
			## rivals and defender are the units trying to enter into or stay
			## in the same area as 'u'
			rivals = u_order.get_rivals()
			defender = u_order.get_defender()
			info += u"Unit has %s rivals.\n" % len(rivals)
			conflict_area = u.get_attacked_area()
			##
			if conflict_area.standoff:
				info += u"Trying to enter a standoff area.\n"
				#u.delete_order()
				continue
			else:
				standoff = False
			## if there is a rival with the same strength as 'u', there is a
			## standoff.
			## if not, check for defenders
			for r in rivals:
				strength = Unit.objects.get_with_strength(self, id=r.id).strength
				info += u"Rival %s has %s supports.\n" % (r, strength)
				if strength >= s: #in fact, strength cannot be greater
					info += u"Rival wins.\n"
					standoff = True
					exit
				else:
					## the rival is defeated and loses its orders
					info += u"Deleting order of %s.\n" % r
					r.delete_order()
			## if there is a standoff, delete the order and all rivals' orders
			if standoff:
				conflict_area.mark_as_standoff()
				info += u"Standoff in %s.\n" % conflict_area
				for r in rivals:
					r.delete_order()
				u.delete_order()
				continue
			## if there is no standoff, rivals allow the unit to enter the area
			## then check what the defenders think
			else:
				## if there is a defender
				if isinstance(defender, Unit):
					## this is a hack to prevent a unit from invading a friend
					## a 'friend enemy' is always as strong as the invading unit
					if defender.player == u.player:
						strength = s
						info += u"Defender is a friend.\n"
					else:
						strength = Unit.objects.get_with_strength(self,
														id=defender.id).strength
					info += u"Defender %s has %s supports.\n" % (defender, strength)
					## if attacker is not as strong as defender
					if strength >= s:
						## if the defender is trying to exchange areas with
						## the attacker, there is a standoff in the defender's
						## area
						if defender.get_attacked_area() == u.area:			
							defender.area.mark_as_standoff()
							info += u"Trying to exchange areas.\n"
							info += u"Standoff in %s.\n" % defender.area
						else:
						## the invasion is conditioned to the defender leaving
							info += u"%s's movement is conditioned.\n" % u
							inv = Invasion(u, defender.area)
							if u_order.code == '-':
								info += u"%s might get empty.\n" % u.area
								conditioned_origins.append(u.area)
							elif u_order.code == '=':
								inv.conversion = u_order.type
							conditioned_invasions.append(inv)
					## if the defender is weaker, the area is invaded and the
					## defender must retreat
					else:
						defender.must_retreat = u.area.board_area.code
						defender.save()
						if u_order.code == '-':
							u.invade_area(defender.area)
							info += u"Invading %s.\n" % defender.area
						elif u_order.code == '=':
							info += u"Converting into %s.\n" % u_order.type
							u.convert(u_order.type)
						defender.delete_order()
				## no defender means either that the area is empty *OR*
				## that there is a unit trying to leave the area
				else:
					info += u"There is no defender.\n"
					try:
						unit_leaving = Unit.objects.get(type__in=['A','F'],
												area=conflict_area)
					except ObjectDoesNotExist:
						## if the province is empty, invade it
						info += u"Province is empty.\n"
						if u_order.code == '-':
							info += u"Invading %s.\n" % conflict_area
							u.invade_area(conflict_area)
						elif u_order.code == '=':
							info += u"Converting into %s.\n" % u_order.type
							u.convert(u_order.type)
					else:
						## if the area is not empty, and the unit in province
						## is not a friend, and the attacker has supports
						## it invades the area, and the unit in the province
						## must retreat (if it invades another area, it mustnt).
						if unit_leaving.player != u.player and u.strength > 0:
							info += u"There is a unit in %s, but attacker is supported.\n" % conflict_area
							unit_leaving.must_retreat = u.area.board_area.code
							unit_leaving.save()
							if u_order.code == '-':
								u.invade_area(unit_leaving.area)
								info += u"Invading %s.\n" % unit_leaving.area
							elif u_order.code == '=':
								info += u"Converting into %s.\n" % u_order.type
								u.convert(u_order.type)
						## if the area is not empty, the invasion is conditioned
						else:
							info += u"Area is not empty and attacker isn't supported, or there is a friend\n"
							info += u"%s movement is conditioned.\n" % u
							inv = Invasion(u, conflict_area)
							if u_order.code == '-':
								info += u"%s might get empty.\n" % u.area
								conditioned_origins.append(u.area)
							elif u_order.code == '=':
								inv.conversion = u_order.type
							conditioned_invasions.append(inv)
		## at this point, all the 'easy' movements and conversions have been
		## made, and we have a conditioned_invasions sequence
		## conditioned_invasions is a list of Invasion objects:
		##
		## in a first iteration, we solve the conditioned_invasions directed
		## to now empty areas
		try_empty = True
		while try_empty:
			info += u"Looking for possible, conditioned invasions.\n"
			try_empty = False
			for ci in conditioned_invasions:
				if ci.area.province_is_empty():
					info += u"Found empty area in %s.\n" % ci.area
					if ci.unit.area in conditioned_origins:
						conditioned_origins.remove(ci.unit.area)
					if ci.conversion == '':
						ci.unit.invade_area(ci.area)
					else:
						ci.unit.convert(ci.conversion)
					conditioned_invasions.remove(ci)
					try_empty = True
					break
		## in a second iteration, we cancel the conditioned_invasions that
		## cannot be made
		try_impossible = True
		while try_impossible:
			info += u"Looking for impossible, conditioned.\n"
			try_impossible = False
			for ci in conditioned_invasions:
				if not ci.area in conditioned_origins:
					## the unit is trying to invade an area with a stationary
					## unit
					info += u"Found impossible invasion in %s.\n" % ci.area
					ci.area.mark_as_standoff()
					conditioned_invasions.remove(ci)
					if ci.unit.area in conditioned_origins:
						conditioned_origins.remove(ci.unit.area)
					try_impossible = True
					break
		## at this point, if there are any conditioned_invasions, they form
		## closed circuits, so all of them should be carried out
		info += u"Resolving closed circuits.\n"
		for ci in conditioned_invasions:
			if ci.conversion == '':
				info += u"%s invades %s.\n" % (ci.unit, ci.area)
				ci.unit.invade_area(ci.area)
			else:
				info += u"%s converts into %s.\n" % (ci.unit, ci.conversion)
				ci.unit.convert(ci.conversion)
		## units in 'holding' that don't need to retreat, can put rebellions down
		for h in holding:
			if h.must_retreat != '':
				continue
			else:
				reb = h.area.has_rebellion(h.player, same=True)
				if reb:
					info += u"Rebellion in %s is put down.\n" % h.area
					reb.delete()
		
		info += u"End of conflicts processing"
		return info

	def resolve_sieges(self):
		## get units that are besieging but do not besiege a second time
		info = u"Step 6: Process sieges.\n"
		broken = Unit.objects.filter(Q(player__game=self,
									besieging__exact=True),
									~Q(order__code__exact='B'))
		for b in broken:
			info += u"Siege of %s is discontinued.\n" % b
			b.besieging = False
			b.save()		
		## get besieging units
		besiegers = Unit.objects.filter(player__game=self,
										order__code__exact='B')
		for b in besiegers:
			info += u"%s besieges " % b
			mode = ''
			if b.player.assassinated:
				info += u"\n%s belongs to an assassinated player.\n" % b
				continue
			try:
				defender = Unit.objects.get(player__game=self,
										type__exact='G',
										area=b.area)
			except:
				reb = b.area.has_rebellion(b.player, same=True)
				if reb and reb.garrisoned:
					mode = 'rebellion'
					info += u"a rebellion "
				else:
					ok = False
					info += u"Besieging an empty city. Ignoring.\n"
					b.besieging = False
					b.save()
					continue
			else:
				mode = 'garrison'
			if mode != '':
				if b.besieging:
					info += u"for second time.\n"
					b.besieging = False
					info += u"Siege is successful. "
					if mode == 'garrison':
						info += u"Garrison disbanded.\n" 
						if signals:
							signals.unit_surrendered.send(sender=defender)
						else:
							self.log_event(UnitEvent, type=defender.type,
												area=defender.area.board_area,
												message=2)
						defender.delete()
					elif mode == 'rebellion':
						info += u"Rebellion is put down.\n"
						reb.delete()
					b.save()
				else:
					info += u"for first time.\n"
					b.besieging = True
					if signals:
						signals.siege_started.send(sender=b)
					else:
						self.log_event(UnitEvent, type=b.type, area=b.area.board_area, message=3)
					if mode == 'garrison' and defender.player.assassinated:
						info += u"Player is assassinated. Garrison surrenders\n"
						if signals:
							signals.unit_surrendered.send(sender=defender)
						else:
							self.log_event(UnitEvent, type=defender.type,
												area=defender.area.board_area,
												message=2)
						defender.delete()
						b.besieging = False	
					b.save()
			b.delete_order()
		return info
	
	def announce_retreats(self):
		info = u"Step 7: Retreats\n"
		retreating = Unit.objects.filter(player__game=self).exclude(must_retreat__exact='')
		for u in retreating:
			info += u"%s must retreat.\n" % u
			if signals:
				signals.forced_to_retreat.send(sender=u)
			else:
				self.log_event(UnitEvent, type=u.type, area=u.area.board_area, message=1)
		return info

	def process_orders(self):
		""" Run a batch of methods in the correct order to process all the orders.
		"""

		info = u"Processing orders in game %s\n" % self.slug
		info += u"------------------------------\n\n"
		## delete all orders that were not confirmed
		Order.objects.filter(unit__player__game=self, confirmed=False).delete()
		## delete all orders sent by players that don't control the unit
		if self.configuration.finances:
			Order.objects.filter(player__game=self).exclude(player=F('unit__player')).delete()
		## resolve =G that are not opposed
		info += self.resolve_auto_garrisons()
		info += u"\n"
		## delete supports from units in conflict areas
		info += self.filter_supports()
		info += u"\n"
		## delete convoys that will be invaded
		info += self.filter_convoys()
		info += u"\n"
		## delete attacks to areas that are not reachable
		info += self.filter_unreachable_attacks()
		info += u"\n"
		## process conflicts
		info += self.resolve_conflicts()
		info += u"\n"
		## resolve sieges
		info += self.resolve_sieges()
		info += u"\n"
		info += self.announce_retreats()
		info += u"--- END ---\n"
		if logging:
			logging.info(info)
		turn_log = TurnLog(game=self, year=self.year,
							season=self.season,
							phase=self.phase,
							log=info)
		turn_log.save()

	def process_retreats(self):
		""" From the saved RetreaOrders, process the retreats. """

		disbands = RetreatOrder.objects.filter(unit__player__game=self, area__isnull=True)
		for d in disbands:
			d.unit.delete()
		retreat_areas = GameArea.objects.filter(game=self, retreatorder__isnull=False).annotate(
												number_of_retreats=Count('retreatorder'))
		for r in retreat_areas:
			if r.number_of_retreats > 1:
				disbands = RetreatOrder.objects.filter(area=r)
				for d in disbands:
					d.unit.delete()
			else:
				order = RetreatOrder.objects.get(area=r)
				unit = order.unit
				unit.retreat(order.area)
				order.delete()
	
	def update_controls(self):
		""" Checks which GameAreas have been controlled by a Player and update them.
		"""

		for area in GameArea.objects.filter(Q(game=self) &
								Q(unit__isnull=False) &
								(Q(board_area__is_sea=False) |
								Q(board_area__code__exact='VEN'))).distinct():
			players = self.player_set.filter(unit__area=area).distinct()
			if len(players) > 2:
				err_msg = "%s units in %s (game %s)" % (len(players),area, self)
				raise exceptions.WrongUnitCount(err_msg)
			elif len(players) == 1 and players[0].user:
				if area.player != players[0]:
					area.player = players[0]
					area.save()
					if signals:
						signals.area_controlled.send(sender=area)
					else:
						self.log_event(ControlEvent, country=area.player.country, area=area.board_area)
			else:
					area.player = None
					area.save()

	##---------------------
	## logging methods
	##---------------------

	def log_event(self, e, **kwargs):
		## TODO: CATCH ERRORS
		#event = e(game=self, year=self.year, season=self.season, phase=self.phase, **kwargs)
		#event.save()
		pass


	##------------------------
	## game ending methods
	##------------------------

	def check_winner(self):
		""" Returns True if at least one player has reached the cities_to_win. """

		for p in self.player_set.filter(user__isnull=False):
			if p.number_of_cities() >= self.cities_to_win:
				return True
		return False
		
	def assign_scores(self):
		qual = []
		for p in self.player_set.filter(user__isnull=False):
			qual.append((p, p.number_of_cities()))
		## sort the players by their number of cities, less cities go first
		qual.sort(cmp=lambda x,y: cmp(x[1], y[1]), reverse=False)
		zeros = len(qual) - len(SCORES)
		assignation = SCORES + [0] * zeros
		for s in assignation:
			try:
				q = qual.pop()
			except:
				exit
			else:
				# add the number of cities to the score
				score = Score(user=q[0].user, game=q[0].game,
							country=q[0].country,
							points = s + q[1],
							cities = q[1])
				score.save()
				## add the points to the profile total_score
				score.user.get_profile().total_score += score.points
				score.user.get_profile().save()
				## highest score = last score
				while qual != [] and qual[-1][1] == q[1]:
					tied = qual.pop()
					score = Score(user=tied[0].user, game=tied[0].game,
								country=tied[0].country,
								points = s + tied[1],
								cities = tied[1])
					score.save()
					## add the points to the profile total_score
					score.user.get_profile().total_score += score.points
					score.user.get_profile().save()

	def game_over(self):
		self.phase = PHINACTIVE
		self.finished = datetime.now()
		self.save()
		self.notify_players("game_over", {"game": self})
		self.tweet_message("The game %(game)s is over" % {'game': self.slug})
		self.tweet_results()
		self.clean_useless_data()

	def clean_useless_data(self):
		""" In a finished game, delete all the data that is not going to be used
		anymore. """

		self.player_set.all().delete()
		self.gamearea_set.all().delete()
	
	##------------------------
	## notification methods
	##------------------------

	def notify_players(self, label, extra_context=None, on_site=True):
		if notification:
			users = User.objects.filter(player__game=self,
										player__eliminated=False)
			if self.fast:
				notification.send_now(users, label, extra_context, on_site)
			else:
				notification.send(users, label, extra_context, on_site)

	def tweet_message(self, message):
		if twitter_api:
			#thread.start_new_thread(twitter_api.PostUpdate, (message,))
			twitter_api.PostUpdate(message)

	def tweet_results(self):
		if twitter_api:
			#winners = self.player_set.order_by('-score')
			winners = self.score_set.order_by('-points')
			message = "'%s' - Winner: %s; 2nd: %s; 3rd: %s" % (self.slug,
							winners[0].user,
							winners[1].user,
							winners[2].user)
			self.tweet_message(message)

if twitter_api and settings.TWEET_NEW_GAME:
	def tweet_new_game(sender, instance, created, **kw):
		if twitter_api and isinstance(instance, Game):
			if created == True:
				message = "New game: http://www.condottierigame.com%s" % instance.get_absolute_url()
				twitter_api.PostUpdate(message)

	models.signals.post_save.connect(tweet_new_game, sender=Game)

class GameArea(models.Model):
	""" This class defines the actual game areas where each game is played. """

	game = models.ForeignKey(Game)
	board_area = models.ForeignKey(Area)
	## player is who controls the area, if any
	player = models.ForeignKey('Player', blank=True, null=True)
	standoff = models.BooleanField(default=False)
	famine = models.BooleanField(default=False)

	def abbr(self):
		return "%s (%s)" % (self.board_area.code, self.board_area.name)

	def __unicode__(self):
		#return self.board_area.name
		#return "(%(code)s) %(name)s" % {'name': self.board_area.name, 'code': self.board_area.code}
		return unicode(self.board_area)

	def accepts_type(self, type):
		return self.board_area.accepts_type(type)
	
	def possible_reinforcements(self):
		""" Returns a list of possible unit types for an area. """

		existing_types = []
		result = []
		units = self.unit_set.all()
		for unit in units:
	        	existing_types.append(unit.type)
		if self.accepts_type('G') and not "G" in existing_types:
			result.append('G')
		if self.accepts_type('F') and not ("A" in existing_types or "F" in existing_types):
			result.append('F')
		if self.accepts_type('A') and not ("A" in existing_types or "F" in existing_types):
			result.append('A')
		return result

	def mark_as_standoff(self):
		if signals:
			signals.standoff_happened.send(sender=self)
		else:
			self.game.log_event(StandoffEvent, area=self.board_area)
		self.standoff = True
		self.save()

	def province_is_empty(self):
		return self.unit_set.exclude(type__exact='G').count() == 0

	def get_adjacent_areas(self, include_self=False):
		""" Returns a queryset with all the adjacent GameAreas """
		if include_self:
			cond = Q(board_area__borders=self.board_area, game=self.game) | Q(id=self.id)
		else:
			cond = Q(board_area__borders=self.board_area, game=self.game)
		adj = GameArea.objects.filter(cond).distinct()
		return adj
	
	def has_rebellion(self, player, same=True):
		""" If there is a rebellion in the area, either against the player or
		against any other player, returns the rebellion. """
		try:
			if same:
				reb = Rebellion.objects.get(area=self, player=player)
			else:
				reb = Rebellion.objects.exclude(player=player).get(area=self)
		except ObjectDoesNotExist:
			return False
		return reb

	def check_assassination_rebellion(self):
		""" When a player is assassinated this function checks if a new
		rebellion appears in the game area. """
		if self.board_area.is_sea:
			return False
		## if there are units of other players in the area, there is no rebellion
		## this is not too clear in the rules
		if Unit.objects.filter(area=self).exclude(player=self.player).count() > 0:
			return False
		if not self.has_rebellion(self.player):
			result = False
			die = dice.roll_1d6()
			try:
				Unit.objects.get(area=self, player=self.player)
			except ObjectDoesNotExist:
				occupied = False
			else:
				occupied = True
			## the province is a home province
			if self in self.player.home_country():
				if occupied and die == 1:
					result = True
				elif not occupied and die in (1, 2):
					result = True
			## the province is conquered
			else:
				if occupied and die in (1, 2, 3):
					result = True
				elif not occupied and die != 6:
					result = True
			if result:
				rebellion = Rebellion(area=self)
				rebellion.save()
		return False
			

def check_min_karma(sender, instance=None, **kwargs):
	if isinstance(instance, CondottieriProfile):
		if instance.karma < settings.KARMA_TO_JOIN:		
			players = Player.objects.filter(user=instance.user,
											game__slots__gt=0)
			for p in players:
				game = p.game
				p.delete()
				game.slots += 1
				game.save()
	
models.signals.post_save.connect(check_min_karma, sender=CondottieriProfile)


class Score(models.Model):
	""" This class defines the scores that a user got in a finished game. """

	user = models.ForeignKey(User)
	game = models.ForeignKey(Game)
	country = models.ForeignKey(Country)
	points = models.PositiveIntegerField(default=0)
	cities = models.PositiveIntegerField(default=0)
	position = models.PositiveIntegerField(default=0)

	def __unicode__(self):
		return "%s (%s)" % (self.user, self.game)

class Player(models.Model):
	""" This class defines the relationship between a User and a Game. """

	user = models.ForeignKey(User, blank=True, null=True) # can be null because of autonomous units
	game = models.ForeignKey(Game)
	country = models.ForeignKey(Country, blank=True, null=True)
	done = models.BooleanField(default=False)
	eliminated = models.BooleanField(default=False)
	conqueror = models.ForeignKey('self', related_name='conquered', blank=True, null=True)
	excommunicated = models.PositiveIntegerField(blank=True, null=True)
	assassinated = models.BooleanField(default=False)
	defaulted = models.BooleanField(default=False)
	ducats = models.PositiveIntegerField(default=0)
	double_income = models.BooleanField(default=False)
	may_excommunicate = models.BooleanField(default=False)
	static_name = models.CharField(max_length=20, default="")
	step = models.PositiveIntegerField(default=0)

	def __unicode__(self):
		if self.user:
			return "%s (%s)" % (self.user, self.game)
		else:
			return "Autonomous in %s" % self.game

	def get_language(self):
		if self.user:
			return self.user.account_set.all()[0].get_language_display()
		else:
			return ''
	
	def get_setups(self):
		return Setup.objects.filter(scenario=self.game.scenario,
				country=self.country).select_related()
	
	def home_control_markers(self):
		""" Assigns each GameArea the player as owner. """
		GameArea.objects.filter(game=self.game,
								board_area__home__scenario=self.game.scenario,
								board_area__home__country=self.country).update(player=self)
	
	def place_initial_units(self):
		for s in self.get_setups():
			try:
				a = GameArea.objects.get(game=self.game, board_area=s.area)
			except:
				print "Error 2: Area not found!"
			else:
				#a.player = self
				#a.save()
				if s.unit_type:
					new_unit = Unit(type=s.unit_type, area=a, player=self, paid=False)
					new_unit.save()
	
	def number_of_cities(self):
		""" Returns the number of cities controlled by the player. """

		cities = GameArea.objects.filter(player=self, board_area__has_city=True)
		return len(cities)

	def number_of_units(self):
		## this funcion is deprecated
		return self.unit_set.all().count()

	def placed_units_count(self):
		return self.unit_set.filter(placed=True).count()
	
	def units_to_place(self):
		""" Return the number of units that the player must place. Negative if
		the player has to remove units.
		"""

		if not self.user:
			return 0
		cities = self.number_of_cities()
		if self.game.configuration.famine:
			famines = self.gamearea_set.filter(famine=True, board_area__has_city=True).exclude(unit__type__exact='G').count()
			cities -= famines
		units = len(self.unit_set.all())
		place = cities - units
		slots = len(self.get_areas_for_new_units())
		if place > slots:
			place = slots
		return place
	
	def home_country(self):
		""" Returns a queryset with Game Areas in home country. """

		return GameArea.objects.filter(game=self.game,
									board_area__home__scenario=self.game.scenario,
									board_area__home__country=self.country,
									board_area__home__is_home=True)

	def controlled_home_country(self):
		""" Returns a queryset with GameAreas in home country controlled by player.
		"""

		return self.home_country().filter(player=self)

	def controlled_home_cities(self):
		""" Returns a queryset with GameAreas in home country, with city, 
		controlled by the player """
		return self.controlled_home_country().filter(board_area__has_city=True)

	def get_areas_for_new_units(self, finances=False):
		""" Returns a queryset with the GameAreas that accept new units. """

		if self.game.configuration.conquering:
			conq_countries = []
			for c in self.conquered.all():
				conq_countries.append(c.country)
			areas = GameArea.objects.filter(Q(player=self) &
										Q(board_area__has_city=True) &
										Q(board_area__home__scenario=self.game.scenario) &
										Q(board_area__home__is_home=True) &
										Q(famine=False) &
										(Q(board_area__home__country=self.country) |
										Q(board_area__home__country__in=conq_countries)))
		else:
			areas = self.controlled_home_cities().exclude(famine=True)
		excludes = []
		for a in areas:
			if a.board_area.is_fortified and len(a.unit_set.all()) > 1:
				excludes.append(a.id)
			elif not a.board_area.is_fortified and len(a.unit_set.all()) > 0:
				excludes.append(a.id)
		if finances:
			## exclude areas where a unit has not been paid
			for u in self.unit_set.filter(placed=True, paid=False):
				excludes.append(u.area.id)
		areas = areas.exclude(id__in=excludes)
		return areas

	def cancel_orders(self):
		""" Delete all the player's orders """
		self.order_set.all().delete()
	
	def check_eliminated(self):
		""" Before updating controls, check if the player is eliminated.

		A player will be eliminated, **unless**:
		- He has at least one empty **and** controlled home city, **OR**
		- One of his home cities is occupied **only** by him.
		"""

		if not self.user:
			return False
		## find a home city controlled by the player, and empty
		cities = self.controlled_home_cities().filter(unit__isnull=True).count()
		if cities > 0:
			print "%s has empty controlled home cities" % self
			return False
		## find a home city occupied only by the player
		enemies = self.game.player_set.exclude(id=self.id)
		occupied = self.game.gamearea_set.filter(unit__player__in=enemies).distinct().values('id')
		safe = self.home_country().filter(unit__player=self).exclude(id__in=occupied).count()
		if safe > 0:
			print "%s has safe cities" % self
			return False
		print "%s is eliminated" % self
		return True

	def eliminate(self):
		""" Eliminates the player and removes units, controls, etc.

		If excommunication rule is being used, clear excommunications.
		.. Warning::
			This only should be used while there's only one country that can excommunicate.
		"""
		
		if self.user:
			self.eliminated = True
			self.save()
			signals.country_eliminated.send(sender=self, country=self.country)
			if logging:
				msg = "Game %s: player %s has been eliminated." % (self.game.pk,
															self.pk)
				logging.info(msg)
			for unit in self.unit_set.all():
				unit.delete()
			for area in self.gamearea_set.all():
				area.player = None
				area.save()
			for rev in self.revolution_set.all():
				rev.delete()
			if self.game.configuration.excommunication:
				if self.country.can_excommunicate:
					self.game.player_set.all().update(excommunicated=None)
		

	def set_conqueror(self, player):
		if player != self:
			signals.country_conquered.send(sender=self, country=self.country)
			if logging:
				msg = "Player %s conquered by player %s" % (self.pk, player.pk)
				logging.info(msg)
			self.conqueror = player
			if self.game.configuration.finances:
				if self.ducats > 0:
					player.ducats = F('ducats') + self.ducats
					player.save()
					self.ducats = 0
			self.save()

	def can_excommunicate(self):
		""" Returns true if player.may_excommunicate and nobody has been
		excommunicated this year.
		"""

		if self.eliminated:
			return False
		if self.game.configuration.excommunication:
			if self.may_excommunicate:
				try:
					Player.objects.get(game=self.game,
									excommunicated=self.game.year)
				except ObjectDoesNotExist:
					return True
				except MultipleObjectsReturned:
					return False
		return False
	
	def excommunicate(self, year=None):
		if year:
			self.excommunicated = year
		else:
			self.excommunicated = self.game.year
		self.save()
		signals.country_excommunicated.send(sender=self)
		if logging:
			msg = "Player %s excommunicated" % self.pk
			logging.info(msg)

	def assassinate(self):
		self.assassinated = True
		self.save()
		signals.player_assassinated.send(sender=self)

	def end_phase(self, forced=False):
		self.done = True
		self.step = 0
		self.save()
		if not forced:
			if not self.game.fast and self.game.check_bonus_time():
				## get a karma bonus
				#self.user.stats.adjust_karma(1)
				self.user.get_profile().adjust_karma(1)
			## delete possible revolutions
			Revolution.objects.filter(government=self).delete()
			msg = "Player %s ended phase" % self.pk
		else:
			self.force_phase_change()
			msg = "Player %s forced to end phase" % self.pk
		#self.game.check_next_phase()
		if logging:
			logging.info(msg)

	def new_phase(self):
		## check that the player is not autonomous and is not eliminated
		if self.user and not self.eliminated:
			if self.game.phase == PHREINFORCE and not self.game.configuration.finances:
				if self.units_to_place() == 0:
					self.done = True
				else:
					self.done = False
			elif self.game.phase == PHORDERS:
				units = self.unit_set.all().count()
				if units <= 0:
					self.done = True
				else:
					self.done = False
			elif self.game.phase == PHRETREATS:
				retreats = self.unit_set.exclude(must_retreat__exact='').count()
				if retreats == 0:
					self.done = True
				else:
					self.done = False
			else:
				self.done = False
			self.save()

	def next_phase_change(self):
		""" Returns the time that the next forced phase change would happen,
		if this were the only player (i.e. only his own karma is considered)
		"""
		
		if self.game.fast:
			karma = 100.
		else:
			karma = float(self.user.get_profile().karma)
		if karma > 100:
			if self.game.phase == PHORDERS:
				k = 1 + (karma - 100) / 200
			else:
				k = 1
		else:
			k = karma / 100
		time_limit = self.game.time_limit * k
		
		duration = timedelta(0, time_limit)

		return self.game.last_phase_change + duration
	
	def time_exceeded(self):
		""" Returns true if the player has exceeded his own time, and he is playing because
		other players have not yet finished. """

		return self.next_phase_change() < datetime.now()

	def get_time_status(self):
		""" Returns a string describing the status of the player depending on the time limits.
		This string is to be used as a css class to show the time """
		now = datetime.now()
		bonus = self.game.get_bonus_deadline()
		if now <= bonus:
			return 'bonus_time'
		safe = self.next_phase_change()
		if now <= safe:
			return 'safe_time'
		return 'unsafe_time'
	
	def force_phase_change(self):
		## the player didn't take his actions, so he loses karma
		if not self.game.fast:
			self.user.get_profile().adjust_karma(-10)
		## if there is a revolution with an overthrowing player, change users
		try:
			rev = Revolution.objects.get(government=self)
		except ObjectDoesNotExist:
			if not self.game.fast:
				## create a new possible revolution
				rev = Revolution(government=self)
				rev.save()
				logging.info("New revolution for player %s" % self)
		else:
			if rev.opposition:
				if notification:
					## notify the old player
					user = [self.user,]
					extra_context = {'game': self.game,}
					notification.send(user, "lost_player", extra_context, on_site=True)
					## notify the new player
					user = [rev.opposition]
					if self.game.fast:
						notification.send_now(user, "got_player", extra_context)	
					else:
						notification.send(user, "got_player", extra_context)
				self.user = rev.opposition
				logging.info("Government of %s is overthrown" % self.country)
				if signals:
					signals.government_overthrown.send(sender=self)
				else:
					self.game.log_event(CountryEvent,
								country=self.country,
								message=0)
				self.save()
				rev.delete()
				self.user.get_profile().adjust_karma(10)

	def unread_count(self):
		""" Gets the number of unread received letters """
		
		if condottieri_messages:
			return condottieri_messages.models.Letter.objects.filter(recipient_player=self, read_at__isnull=True, recipient_deleted_at__isnull=True).count()
		else:
			return 0
	
	
	##
	## Income calculation
	##
	def get_control_income(self, die, majors_ids, rebellion_ids):
		""" Gets the sum of the control income of all controlled AND empty
		provinces. Note that provinces affected by plague don't genearate
		any income"""
		gamearea_ids = self.gamearea_set.filter(famine=False).exclude(id__in=rebellion_ids).values_list('board_area', flat=True)
		income = Area.objects.filter(id__in = gamearea_ids).aggregate(Sum('control_income'))

		i =  income['control_income__sum']
		if i is None:
			return 0
		
		v = 0
		for a in majors_ids:
			if a in gamearea_ids:
				city = Area.objects.get(id=a)
				v += finances.get_ducats(city.code, die)

		return income['control_income__sum'] + v

	def get_occupation_income(self):
		""" Gets the sum of the income of all the armies and fleets in not controlled areas """
		units = self.unit_set.exclude(type="G").exclude(area__famine=True)
		units = units.filter(~Q(area__player=self) | Q(area__player__isnull=True))

		i = units.count()
		if i > 0:
			return i
		return 0

	def get_garrisons_income(self, die, majors_ids, rebellion_ids):
		""" Gets the sum of the income of all the non-besieged garrisons in non-controlled areas
		"""
		## get garrisons in non-controlled areas
		cond = ~Q(area__player=self)
		cond |= Q(area__player__isnull=True)
		cond |= (Q(area__player=self, area__famine=True))
		cond |= (Q(area__player=self, area__id__in=rebellion_ids))
		garrisons = self.unit_set.filter(type="G")
		garrisons = garrisons.filter(cond)
		garrisons = garrisons.values_list('area__board_area__id', flat=True)
		if len(garrisons) > 0:
			## get ids of gameareas where garrisons are under siege
			sieges = Unit.objects.filter(player__game=self.game, besieging=True)
			sieges = sieges.values_list('area__board_area__id', flat=True)
			## get the income
			income = Area.objects.filter(id__in=garrisons).exclude(id__in=sieges)
			if income.count() > 0:
				v = 0
				for a in income:
					if a.id in majors_ids:
						v += finances.get_ducats(a.code, die)
				income = income.aggregate(Sum('garrison_income'))
				return income['garrison_income__sum'] + v
		return 0

	def get_variable_income(self, die):
		""" Gets the variable income for the country """
		v = finances.get_ducats(self.static_name, die, self.double_income)
		## the player gets the variable income of conquered players
		if self.game.configuration.conquering:
			conquered = self.game.player_set.filter(conqueror=self)
			for c in conquered:
				v += finances.get_ducats(c.static_name, die, c.double_income)

		return v

	def get_income(self, die, majors_ids):
		""" Gets the total income in one turn """
		rebellion_ids = Rebellion.objects.filter(player=self).values_list('area', flat=True)
		income = self.get_control_income(die, majors_ids, rebellion_ids)
		income += self.get_occupation_income()
		income += self.get_garrisons_income(die, majors_ids, rebellion_ids)
		income += self.get_variable_income(die)
		return income

	def add_ducats(self, d):
		""" Adds d to the ducats field of the player."""
		self.ducats = F('ducats') + d
		self.save()
		signals.income_raised.send(sender=self, ducats=d)
		if logging:
			msg = "Player %s raised %s ducats." % (self.pk, d)
			logging.info(msg)

	def get_credit(self):
		""" Returns the number of ducats that the player can borrow from the bank. """
		if self.defaulted:
			return 0
		credit = self.gamearea_set.count() + self.unit_set.count()
		if credit > 25:
			credit = 25
		return credit

class Revolution(models.Model):
	""" A Revolution instance means that ``government`` is not playing, and
	``opposition`` is trying to replace it.
	"""

	government = models.ForeignKey(Player)
	opposition = models.ForeignKey(User, blank=True, null=True)

	def __unicode__(self):
		return "%s" % self.government

def notify_overthrow_attempt(sender, instance, created, **kw):
	if notification and isinstance(instance, Revolution) and not created:
		user = [instance.government.user,]
		extra_context = {'game': instance.government.game,}
		notification.send(user, "overthrow_attempt", extra_context , on_site=True)

models.signals.post_save.connect(notify_overthrow_attempt, sender=Revolution)

class UnitManager(models.Manager):
	def get_with_strength(self, game, **kwargs):
		u = self.get_query_set().get(**kwargs)
		query = Q(unit__player__game=game,
				  code__exact='S',
				  subunit=u)
		u_order = u.get_order()
		if not u_order:
			query &= Q(subcode__exact='H')
		else:
			if u_order.code in ('', 'H', 'S', 'C', 'B'): #unit is holding
				query &= Q(subcode__exact='H')
			elif u_order.code == '=':
				query &= Q(subcode__exact='=',
						   subtype=u_order.type)
			elif u_order.code == '-':
				query &= Q(subcode__exact='-',
						   subdestination=u_order.destination)
		support = Order.objects.filter(query).count()
		if game.configuration.finances:
			if not u_order or u_order.code in ('', 'H', 'S', 'C', 'B'):
				if u.area.has_rebellion(u.player, same=True):
					support -= 1
		u.strength = support
		return u

	def list_with_strength(self, game):
		from django.db import connection
		cursor = connection.cursor()
		cursor.execute("SELECT u.id, u.type, u.area_id, u.player_id, u.besieging, u.must_retreat, u.placed, u.paid, \
		o.code, o.destination_id, o.type \
		FROM (machiavelli_player p INNER JOIN machiavelli_unit u on p.id=u.player_id) \
		LEFT JOIN machiavelli_order o ON u.id=o.unit_id \
		WHERE p.game_id=%s" % game.id)
		result_list = []
		for row in cursor.fetchall():
			holding = False
			support_query = Q(unit__player__game=game,
							  code__exact='S',
							  subunit__pk=row[0])
			if row[8] in (None, '', 'H', 'S', 'C', 'B'): #unit is holding
				support_query &= Q(subcode__exact='H')
				holding = True
			elif row[8] == '=':
				support_query &= Q(subcode__exact='=',
						   		subtype__exact=row[10])
			elif row[8] == '-':
				support_query &= Q(subcode__exact='-',
								subdestination__pk__exact=row[9])
			support = Order.objects.filter(support_query).count()
			unit = self.model(id=row[0], type=row[1], area_id=row[2],
							player_id=row[3], besieging=row[4],
							must_retreat=row[5], placed=row[6], paid=row[7])
			if game.configuration.finances:
				if holding and unit.area.has_rebellion(unit.player, same=True):
					support -= 1
			unit.strength = support
			result_list.append(unit)
		result_list.sort(cmp=lambda x,y: cmp(x.strength, y.strength), reverse=True)
		return result_list

class Unit(models.Model):
	""" This class defines a unit in a game, its location and status. """

	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	area = models.ForeignKey(GameArea)
	player = models.ForeignKey(Player)
	besieging = models.BooleanField(default=0)
	## must_retreat contains the code, if any, of the area where the attack came from
	must_retreat = models.CharField(max_length=5, blank=True, default='')
	placed = models.BooleanField(default=True)
	paid = models.BooleanField(default=True)
	objects = UnitManager()

	def get_order(self):
		""" If the unit has more than one order, raises an error. If not, return the order.
		When this method is called, each unit should have 0 or 1 order """
		try:
			order = Order.objects.get(unit=self)
		except MultipleObjectsReturned:
			raise MultipleObjectsReturned
		except:
			return None
		else:
			return order
	
	def get_attacked_area(self):
		""" If the unit has orders, get the attacked area, if any. This method is
		only a proxy of the Order method with the same name.
		"""
		order = self.get_order()
		if order:
			return order.get_attacked_area()
		else:
			return GameArea.objects.none()

	def supportable_order(self):
		supportable = "%s %s" % (self.type, self.area.board_area.code)
		order = self.get_order()
		if not order:
			supportable += " H"
		else:
			if order.code in ('', 'H', 'S', 'C', 'B'): #unit is holding
				supportable += " H"
			elif order.code == '=':
				supportable += " = %s" % order.type
			elif order.code == '-':
				supportable += " - %s" % order.destination.board_area.code
		return supportable

	def place(self):
		self.placed = True
		self.paid = False ## to be unpaid in the next reinforcement phase
		if signals:
			signals.unit_placed.send(sender=self)
		else:
			self.player.game.log_event(NewUnitEvent, country=self.player.country,
								type=self.type, area=self.area.board_area)
		self.save()

	def delete(self):
		if signals:
			signals.unit_disbanded.send(sender=self)
		else:
			self.player.game.log_event(DisbandEvent, country=self.player.country,
								type=self.type, area=self.area.board_area)
		super(Unit, self).delete()
	
	def __unicode__(self):
		return _("%(type)s in %(area)s") % {'type': self.get_type_display(), 'area': self.area}
    
	def get_possible_retreats(self):
		## possible_retreats includes all adjancent, non-standoff areas, and the
		## same area where the unit is located (convert to garrison)
		cond = Q(game=self.player.game)
		cond = cond & Q(standoff=False)
		cond = cond & Q(board_area__borders=self.area.board_area)
		## exclude the area where the attack came from
		cond = cond & ~Q(board_area__code__exact=self.must_retreat)
		## exclude areas with 'A' or 'F'
		cond = cond & ~Q(unit__type__in=['A','F'])
		## for armies, exclude seas
		if self.type == 'A':
			cond = cond & Q(board_area__is_sea=False)
			cond = cond & ~Q(board_area__code__exact='VEN')
		## for fleets, exclude areas that are adjacent but their coasts are not
		elif self.type == 'F':
			exclude = []
			for area in self.area.board_area.borders.all():
				if not area.is_adjacent(self.area.board_area, fleet=True):
					exclude.append(area.id)
			cond = cond & ~Q(board_area__id__in=exclude)
			## for fleets, exclude areas that are not seas or coasts
			cond = cond & ~Q(board_area__is_sea=False, board_area__is_coast=False)
		## add the own area if there is no garrison
		## and the attack didn't come from the city
		## and there is no rebellion in the city
		if self.area.board_area.is_fortified:
			if self.type == 'A' or (self.type == 'F' and self.area.board_area.has_port):
				if self.must_retreat != self.area.board_area.code:
					try:
						Unit.objects.get(area=self.area, type='G')
					except ObjectDoesNotExist:
						try:
							Rebellion.objects.get(area=self.area, garrisoned=True)
						except ObjectDoesNotExist:
							cond = cond | Q(id__exact=self.area.id)
	
		return GameArea.objects.filter(cond).distinct()

	def invade_area(self, ga):
		if signals:
			signals.unit_moved.send(sender=self, destination=ga)
		else:
			self.player.game.log_event(MovementEvent, type=self.type,
										origin=self.area.board_area,
										destination=ga.board_area)
		self.area = ga
		self.must_retreat = ''
		self.save()
		self.check_rebellion()

	def retreat(self, destination):
		if signals:
			signals.unit_retreated.send(sender=self, destination=destination)
		else:
			self.log_event(MovementEvent, type=self.type,
										origin=self.area.board_area,
										destination=destination.board_area)
		if self.area == destination:
			assert self.area.board_area.is_fortified == True, "trying to retreat to a non-fortified city"
			self.type = 'G'
		else:
			self.check_rebellion()
		self.must_retreat = ''
		self.area = destination
		self.save()

	def convert(self, new_type):
		if signals:
			signals.unit_converted.send(sender=self,
										before=self.type,
										after=new_type)
		else:
			self.player.game.log_event(ConversionEvent, area=self.area.board_area,
										before=self.type,
										after=new_type)
		self.type = new_type
		self.must_retreat = ''
		self.save()
		if new_type != 'G':
			self.check_rebellion()

	def check_rebellion(self):
		## if there is a rebellion against other player, put it down
		reb = self.area.has_rebellion(self.player, same=False)
		if reb:
			reb.delete()

	def delete_order(self):
		order = self.get_order()
		if order:
			order.delete()
		return True

	def change_player(self, player):
		assert isinstance(player, Player)
		self.player = player
		self.save()
		self.check_rebellion()
		if signals:
			signals.unit_changed_country.send(sender=self)

	def to_autonomous(self):
		assert self.type == 'G'
		self.player = None
		self.save()
		if signals:
			signals.unit_to_autonomous.send(sender=self)

class Order(models.Model):
	""" This class defines an order from a player to a unit. The order will not be
	effective unless it is confirmed.
	"""

	#unit = models.OneToOneField(Unit)
	unit = models.ForeignKey(Unit)
	code = models.CharField(max_length=1, choices=ORDER_CODES)
	destination = models.ForeignKey(GameArea, blank=True, null=True)
	type = models.CharField(max_length=1, blank=True, null=True, choices=UNIT_TYPES)
	## suborder field is deprecated, and will be removed
	suborder = models.CharField(max_length=15, blank=True, null=True)
	subunit = models.ForeignKey(Unit, related_name='affecting_orders', blank=True, null=True)
	subcode = models.CharField(max_length=1, choices=ORDER_SUBCODES, blank=True, null=True)
	subdestination = models.ForeignKey(GameArea, related_name='affecting_orders', blank=True, null=True)
	subtype = models.CharField(max_length=1, blank=True, null=True, choices=UNIT_TYPES)
	confirmed = models.BooleanField(default=False)
	## player field is to be used when a player buys an enemy unit. It can be null for backwards
	## compatibility
	player = models.ForeignKey(Player, null=True)
	
	def as_dict(self):
		result = {
			'id': self.pk,
			'unit': unicode(self.unit),
			'code': self.get_code_display(),
			'destination': '',
			'type': '',
			'subunit': '',
			'subcode': '',
			'subdestination': '',
			'subtype': ''
		}
		if isinstance(self.destination, GameArea):
			result.update({'destination': unicode(self.destination)})
		if not self.type == None:
			result.update({'type': self.get_type_display()})
		if isinstance(self.subunit, Unit):
			result.update({'subunit': unicode(self.subunit)})
			if not self.subcode == None:
				result.update({'subcode': self.get_subcode_display()})
			if isinstance(self.subdestination, GameArea):
				result.update({'subdestination': unicode(self.subdestination)})
			if not self.subtype == None:
				result.update({'subtype': self.get_subtype_display()})

		return result
	
	def explain(self):
		""" Returns a human readable order.	"""

		if self.code == 'H':
			msg = _("%(unit)s holds its position.") % {'unit': self.unit,}
		elif self.code == '-':
			msg = _("%(unit)s tries to go to %(area)s.") % {
							'unit': self.unit,
							'area': self.destination
							}
		elif self.code == 'B':
			msg = _("%(unit)s besieges the city.") % {'unit': self.unit}
		elif self.code == '=':
			msg = _("%(unit)s tries to convert into %(type)s.") % {
							'unit': self.unit,
							'type': self.get_type_display()
							}
		elif self.code == 'C':
			msg = _("%(unit)s must convoy %(subunit)s to %(area)s.") % {
							'unit': self.unit,
							'subunit': self.subunit,
							'area': self.subdestination
							}
		elif self.code == 'S':
			if self.subcode == 'H':
				msg=_("%(unit)s supports %(subunit)s to hold its position.") % {
							'unit': self.unit,
							'subunit': self.subunit
							}
			elif self.subcode == '-':
				msg = _("%(unit)s supports %(subunit)s to go to %(area)s.") % {
							'unit': self.unit,
							'subunit': self.subunit,
							'area': self.subdestination
							}
			elif self.subcode == '=':
				msg = _("%(unit)s supports %(subunit)s to convert into %(type)s.") % {
							'unit': self.unit,
							'subunit': self.subunit,
							'type': self.get_subtype_display()
							}
		return msg
	
	def confirm(self):
		self.confirmed = True
		self.save()
		if self.code != 'H':
			## do not log Hold orders
			if signals:
				signals.order_placed.send(sender=self)
		if self.code != 'B':
			self.unit.besieging = False
			self.unit.save()

	def format_suborder(self):
		""" Returns a string with the abbreviated code (as in Machiavelli) of
		the suborder.
		"""

		if not self.subunit:
			return ''
		f = "%s %s" % (self.subunit.type, self.subunit.area.board_area.code)
		f += " %s" % self.subcode
		if self.subcode == None and self.subdestination != None:
			f += "- %s" % self.subdestination.board_area.code
		elif self.subcode == '-':
			f += " %s" % self.subdestination.board_area.code
		elif self.subcode == '=':
			f += " %s" % self.subtype
		return f

	def format(self):
		""" Returns a string with the abreviated code (as in Machiavelli) of
		the order.
		"""

		f = "%s %s" % (self.unit.type, self.unit.area.board_area.code)
		f += " %s" % self.code
		if self.code == '-':
			f += " %s" % self.destination.board_area.code
		elif self.code == '=':
			f += " %s" % self.type
		elif self.code == 'S' or self.code == 'C':
			f += " %s" % self.format_suborder()
		return f

	def find_convoy_line(self):
		""" Returns True if there is a continuous line of convoy orders from 
		the origin to the destination of the order.
		"""

		origins = [self.unit.area,]
		destination = self.destination
		## get all areas convoying this order AND the destination
		convoy_areas = GameArea.objects.filter(
						## in this game
						(Q(game=self.unit.player.game) &
						## being sea areas
						Q(board_area__is_sea=True) &
						## with convoy orders
						Q(unit__order__code__exact='C') &
						## convoying this unit
						Q(unit__order__subunit=self.unit) &
						## convoying to this destination
						Q(unit__order__subdestination=self.destination)) |
						## OR being the destination
						Q(id=self.destination.id))
		if len(convoy_areas) <= 1:
			return False
		while 1:
			new_origins = []
			for o in origins:
				borders = GameArea.objects.filter(game=self.unit.player.game,
												board_area__borders=o.board_area)
				for b in borders:
					if b == destination:
						return True
					if b in convoy_areas:
						new_origins.append(b)
			if len(new_origins) == 0:
				return False
			origins = new_origins	
	
	def get_enemies(self):
		""" Returns a Queryset with all the units trying to oppose an advance or
		conversion order.
		"""

		if self.code == '-':
			enemies = Unit.objects.filter(Q(player__game=self.unit.player.game),
										## trying to go to the same area
										Q(order__destination=self.destination) |
										## trying to exchange areas
										(Q(area=self.destination) &
										Q(order__destination=self.unit.area)) |
										## trying to convert in the same area
										(Q(type__exact='G') &
										Q(area=self.destination) &
										Q(order__code__exact='=')) |
										## trying to stay in the area
										(Q(type__in=['A','F']) &
										Q(area=self.destination) &
										(Q(order__isnull=True) |
										Q(order__code__in=['B','H','S','C'])))
										).exclude(id=self.unit.id)
		elif self.code == '=':
			enemies = Unit.objects.filter(Q(player__game=self.unit.player.game),
										## trying to go to the same area
										Q(order__destination=self.unit.area) |
										## trying to stay in the area
										(Q(type__in=['A','F']) & 
										Q(area=self.unit.area) &
										(Q(order__isnull=True) |
										Q(order__code__in=['B','H','S','C','='])
										))).exclude(id=self.unit.id)
			
		else:
			enemies = Unit.objects.none()
		return enemies
	
	def get_rivals(self):
		""" Returns a Queryset with all the units trying to enter the same
		province as the unit that gave this order.
		"""

		if self.code == '-':
			rivals = Unit.objects.filter(Q(player__game=self.unit.player.game),
										## trying to go to the same area
										Q(order__destination=self.destination) |
										## trying to convert in the same area
										(Q(type__exact='G') &
										Q(area=self.destination) &
										Q(order__code__exact='='))
										).exclude(id=self.unit.id)
		elif self.code == '=':
			rivals = Unit.objects.filter(Q(player__game=self.unit.player.game),
										## trying to go to the same area
										Q(order__destination=self.unit.area)
										).exclude(id=self.unit.id)
			
		else:
			rivals = Unit.objects.none()
		return rivals
	
	def get_defender(self):
		""" Returns a Unit trying to stay in the destination area of this order, or
		None.
		"""

		try:
			if self.code == '-':
				defender = Unit.objects.get(Q(player__game=self.unit.player.game),
										## trying to exchange areas
										(Q(area=self.destination) &
										Q(order__destination=self.unit.area)) |
										## trying to stay in the area
										(Q(type__in=['A','F']) &
										Q(area=self.destination) &
										(Q(order__isnull=True) |
										Q(order__code__in=['B','H','S','C'])))
										)
			elif self.code == '=':
				defender = Unit.objects.get(Q(player__game=self.unit.player.game),
										## trying to stay in the area
										(Q(type__in=['A','F']) & 
										Q(area=self.unit.area) &
										(Q(order__isnull=True) |
										Q(order__code__in=['B','H','S','C','='])
										)))
			else:
				defender = Unit.objects.none()
		except ObjectDoesNotExist:
			defender = Unit.objects.none()
		return defender
	
	def get_attacked_area(self):
		""" Returns the game area being attacked by this order. """

		if self.code == '-':
			return self.destination
		elif self.code == '=':
			return self.unit.area
		else:
			return GameArea.objects.none()
	
	def __unicode__(self):
		return self.format()

class RetreatOrder(models.Model):
	""" Defines the area where the unit must try to retreat. If ``area`` is
	blank, the unit will be disbanded.
	"""

	unit = models.ForeignKey(Unit)
	area = models.ForeignKey(GameArea, null=True, blank=True)

	def __unicode__(self):
		return "%s" % self.unit

class ControlToken(models.Model):
	""" Defines the coordinates of the control token for a board area. """

	area = models.OneToOneField(Area)
	x = models.PositiveIntegerField()
	y = models.PositiveIntegerField()

	def __unicode__(self):
		return "%s, %s" % (self.x, self.y)


class GToken(models.Model):
	""" Defines the coordinates of the Garrison token in a board area. """

	area = models.OneToOneField(Area)
	x = models.PositiveIntegerField()
	y = models.PositiveIntegerField()

	def __unicode__(self):
		return "%s, %s" % (self.x, self.y)


class AFToken(models.Model):
	""" Defines the coordinates of the Army and Fleet tokens in a board area."""

	area = models.OneToOneField(Area)
	x = models.PositiveIntegerField()
	y = models.PositiveIntegerField()

	def __unicode__(self):
		return "%s, %s" % (self.x, self.y)

class TurnLog(models.Model):
	""" A TurnLog is text describing the processing of the method
	``Game.process_orders()``.
	"""

	game = models.ForeignKey(Game)
	year = models.PositiveIntegerField()
	season = models.PositiveIntegerField(choices=SEASONS)
	phase = models.PositiveIntegerField(choices=GAME_PHASES)
	timestamp = models.DateTimeField(auto_now_add=True)
	log = models.TextField()

	class Meta:
		ordering = ['-timestamp',]

	def __unicode__(self):
		return self.log

class Configuration(models.Model):
	""" Defines the configuration options for each game. 
	
	At the moment, only some of them are actually implemented.
	"""

	game = models.OneToOneField(Game, verbose_name=_('game'), editable=False)
	finances = models.BooleanField(_('finances'), default=False)
	assassinations = models.BooleanField(_('assassinations'), default=False,
					help_text=_('will enable Finances'))
	bribes = models.BooleanField(_('bribes'), default=False,
					help_text=_('will enable Finances'))
	excommunication = models.BooleanField(_('excommunication'), default=False)
	#disasters = models.BooleanField(_('natural disasters'), default=False)
	special_units = models.BooleanField(_('special units'), default=False,
					help_text=_('will enable Finances and Bribes'))
	strategic = models.BooleanField(_('strategic movement'), default=False)
	lenders = models.BooleanField(_('money lenders'), default=False,
					help_text=_('will enable Finances'))
	conquering = models.BooleanField(_('conquering'), default=False)
	famine = models.BooleanField(_('famine'), default=False)
	plague = models.BooleanField(_('plague'), default=False)

	def __unicode__(self):
		return unicode(self.game)

	def get_enabled_rules(self):
		rules = []
		for f in self._meta.fields:
			if isinstance(f, models.BooleanField):
				if f.value_from_object(self):
					rules.append(unicode(f.verbose_name))
		return rules
	
def create_configuration(sender, instance, created, **kwargs):
    if isinstance(instance, Game) and created:
		config = Configuration(game=instance)
		config.save()

models.signals.post_save.connect(create_configuration, sender=Game)

###
### EXPENSES
###

EXPENSE_TYPES = (
	(0, _("Famine relief")),
	(1, _("Pacify rebellion")),
	(2, _("Conquered province to rebel")),
	(3, _("Home province to rebel")),
	(4, _("Counter bribe")),
	(5, _("Disband autonomous garrison")),
	(6, _("Buy autonomous garrison")),
	(7, _("Convert garrison unit")),
	(8, _("Disband enemy unit")),
	(9, _("Buy enemy unit")),
)

EXPENSE_COST = {
	0: 3,
	1: 12,
	2: 9,
	3: 15,
	4: 3,
	5: 6,
	6: 9,
	7: 9,
	8: 12,
	9: 18,
}

def get_expense_cost(type, unit=None):
	assert type in EXPENSE_COST.keys()
	k = 1
	if type in (5, 6, 7, 8, 9):
		assert isinstance(unit, Unit)
		## if the unit is in a major city
		if unit.type == 'G' and unit.area.board_area.garrison_income > 1:
			k = 2
	return k * EXPENSE_COST[type]
		

class Expense(models.Model):
	""" A player may expend unit to affect some units or areas in the game. """
	player = models.ForeignKey(Player)
	ducats = models.PositiveIntegerField(default=0)
	type = models.PositiveIntegerField(choices=EXPENSE_TYPES)
	area = models.ForeignKey(GameArea, null=True, blank=True)
	unit = models.ForeignKey(Unit, null=True, blank=True)

	def save(self, *args, **kwargs):
		## expenses that need an area
		if self.type in (0, 1, 2, 3):
			assert isinstance(self.area, GameArea), "Expense needs a GameArea"
		## expenses that need a unit
		elif self.type in (4, 5, 6, 7, 8, 9):
			assert isinstance(self.unit, Unit), "Expense needs a Unit"
		else:
			raise ValueError, "Wrong expense type %s" % self.type
		## if no errors raised, save the expense
		super(Expense, self).save(*args, **kwargs)
		if signals:
			signals.expense_paid.send(sender=self)
	
	def __unicode__(self):
		data = {
			'country': self.player.country,
			'area': self.area,
			'unit': self.unit,
		}
		messages = {
			0: _("%(country)s reliefs famine in %(area)s"),
			1: _("%(country)s pacifies rebellion in %(area)s"),
			2: _("%(country)s promotes a rebellion in %(area)s"),
			3: _("%(country)s promotes a rebellion in %(area)s"),
			4: _("%(country)s tries to counter bribe on %(unit)s"),
			5: _("%(country)s tries to disband %(unit)s"),
			6: _("%(country)s tries to buy %(unit)s"),
			7: _("%(country)s tries to turn %(unit)s into an autonomous garrison"),
			8: _("%(country)s tries to disband %(unit)s"),
			9: _("%(country)s tries to buy %(unit)s"),
		}

		if self.type in messages.keys():
			return messages[self.type] % data
		else:
			return "Unknown expense"
	
	def is_bribe(self):
		return self.type in (5, 6, 7, 8, 9)

	def is_allowed(self):
		""" Return true if it's not a bribe or the unit is in a valid area as
		stated in the rules. """
		if self.type in (0, 1, 2, 3, 4):
			return True
		elif self.is_bribe():
			## self.unit must be adjacent to a unit or area of self.player
			## then, find the borders of self.unit
			adjacent = self.unit.area.get_adjacent_areas()

class Rebellion(models.Model):
	"""
	A Rebellion may be placed in a GameArea if finances rules are applied.
	Rebellion.player is the player who controlled the GameArea when the
	Rebellion was placed. Rebellion.garrisoned is True if the Rebellion is
	in a garrisoned city.
	"""
	area = models.ForeignKey(GameArea, unique=True)
	player = models.ForeignKey(Player)
	garrisoned = models.BooleanField(default=False)

	def __unicode__(self):
		return "Rebellion in %(area)s against %(player)s" % {'area': self.area,
														'player': self.player}
	
	def save(self, *args, **kwargs):
		## area must be controlled by a player, who is assigned to the rebellion
		try:
			self.player = self.area.player
		except:
			return False
		## a rebellion cannot be placed in a sea area
		if self.area.board_area.is_sea:
			return False
		## check if the rebellion is to be garrisoned
		if self.area.board_area.is_fortified:
			try:
				Unit.objects.get(area=self.area, type='G')
			except ObjectDoesNotExist:
				self.garrisoned = True
			else:
				## there is a garrison in the city
				if self.area.board_area.code == 'VEN':
					## there cannot be a rebellion in Venice sea area
					return False
		super(Rebellion, self).save(*args, **kwargs)
		if signals:
			signals.rebellion_started.send(sender=self.area)
	
class Loan(models.Model):
	""" A Loan describes a quantity of money that a player borrows from the bank, with a term """
	player = models.OneToOneField(Player)
	debt = models.PositiveIntegerField(default=0)
	season = models.PositiveIntegerField(choices=SEASONS)
	year = models.PositiveIntegerField(default=0)

	def __unicode__(self):
		return "%(player)s ows %(debt)s ducats" % {'player': self.player, 'debt': self.debt, }

class Assassin(models.Model):
	""" An Assassin represents a counter that a Player owns, to murder the leader of a country """
	owner = models.ForeignKey(Player)
	target = models.ForeignKey(Country)

	def __unicode__(self):
		return "%(owner)s may assassinate %(target)s" % {'owner': self.owner, 'target': self.target, }

class Assassination(models.Model):
	""" An Assassination describes an attempt made by a Player to murder the leader of another
	Country, spending some Ducats """
	killer = models.ForeignKey(Player, related_name="assassination_attempts")
	target = models.ForeignKey(Player, related_name="assassination_targets")
	ducats = models.PositiveIntegerField(default=0)

	def __unicode__(self):
		return "%(killer)s tries to kill %(target)s" % {'killer': self.killer, 'target': self.target, }

	def explain(self):
		return _("%(ducats)sd to kill the leader of %(country)s.") % {'ducats': self.ducats,
																	'country': self.target.country}
