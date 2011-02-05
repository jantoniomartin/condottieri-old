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
from django.db.models import permalink, Q, Count
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
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

## machiavelli
from machiavelli.fields import AutoTranslateField
from machiavelli.graphics import make_map
from machiavelli.logging import save_snapshot
import machiavelli.disasters as disasters
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
TIME_LIMITS = (
			#(5*24*60*60, _('5 days')),
			#(4*24*60*60, _('4 days')),
			#(3*24*60*60, _('3 days')),
			(2*24*60*60, _('2 days')),
			(24*60*60, _('1 day')),
			(12*60*60, _('1/2 day')),
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
	cities_to_win = models.PositiveIntegerField(default=15)
	enabled = models.BooleanField(default=False) # this allows me to create the new setups in the admin

	def get_slots(self):
		slots = len(self.setup_set.values('country').distinct()) - 1
		return slots

	def __unicode__(self):
		return self.title

	def get_absolute_url(self):
		return "scenario/%s" % self.id

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
		return result_list

	def highest_score(self):
		""" Returns the Score with the highest points value. """

		if self.slots > 0 or self.phase != PHINACTIVE:
			return Score.objects.none()
		scores = self.score_set.all().order_by('-points')
		return scores[0]

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
			self.home_control_markers()
			self.place_initial_units()
			#self.map_outdated = True
			self.make_map()
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

	def create_game_board(self):
		""" Creates the GameAreas for the Game.	"""

		for a in Area.objects.all():
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

	##--------------------------
	## time controlling methods
	##--------------------------

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

		## get the player with the highest karma, and not done
		if self.phase == PHINACTIVE :
			return False
		highest = self.get_highest_karma()
		if highest <= 100:
			time_limit = self.time_limit * highest / 100
		else:
			time_limit = self.time_limit * (1 + (highest - 100)/200)
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
				#p.force_phase_change()
				if self.phase == PHREINFORCE:
					reinforce = p.units_to_place()
					if reinforce < 0:
						## delete the newest units
						units = Unit.objects.filter(player=p).order_by('-id')[:-reinforce]
						for u in units:
							u.delete()
				elif self.phase == PHORDERS:
					pass
				elif self.phase == PHRETREATS:
					## disband the units that should retreat
					Unit.objects.filter(player=p).exclude(must_retreat__exact='').delete()
				p.end_phase(forced=True)
		
	def check_time_limit(self):
		""" Checks if the time limit has been reached. If yes, force a phase change """

		if not self.phase == PHINACTIVE:
			limit = self.next_phase_change()
			to_limit = limit - datetime.now()
			if to_limit <= timedelta(0, 0):
				self.force_phase_change()
	
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
			next_phase = PHORDERS
		elif self.phase == PHORDERS:
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
				if self.configuration.disasters:
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
				## if natural disasters are enabled, place famine markers
				if self.configuration.disasters:
					self.mark_famine_areas()
			self._next_season()
			if self.season == 1:
				next_phase = PHORDERS
				for p in self.player_set.all():
					if p.units_to_place() != 0:
						next_phase = PHREINFORCE
						break
			else:
				next_phase = PHORDERS
		self.phase = next_phase
		self.last_phase_change = datetime.now()
		#self.map_changed()
		self.save()
		self.make_map()
		self.notify_players("new_phase", {"game": self}, on_site=False)
    
	def check_next_phase(self):
		""" When a player ends its phase, send a signal to the game. This function
		checks if all the players have finished.
		"""

		for p in self.player_set.all():
			if not p.done:
				return False
		self.all_players_done()
		for p in self.player_set.all():
			p.new_phase()

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
		if not self.configuration.disasters:
			return
		codes = disasters.get_famine()
		famine_areas = GameArea.objects.filter(game=self, board_area__code__in=codes)
		for f in famine_areas:
			f.famine=True
			f.save()
			signals.famine_marker_placed.send(sender=f)
	
	def kill_plague_units(self):
		if not self.configuration.disasters:
			return
		codes = disasters.get_plague()
		plague_areas = GameArea.objects.filter(game=self, board_area__code__in=codes)
		for p in plague_areas:
			signals.plague_placed.send(sender=p)
			for u in p.unit_set.all():
				u.delete()
	
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
				attacks = Order.objects.filter((Q(code__exact='-') & Q(destination=s.unit.area)) |
												(Q(code__exact='=') & Q(unit__area=s.unit.area) &
												Q(unit__type__exact='G')))
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
			try:
				## find the defender
				if s.order.code == '-':
					defender = Unit.objects.get(player__game=self,
											area=s.order.destination,
											type__exact='F',
											order__code__exact='C')
				elif s.order.code == '=' and s.area.board_area.code == 'VEN':
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
					try:
						defender.order
					except:
						continue
					else:
						info += u"%s can't convoy.\n" % defender
						defender.delete_order()
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
				g.order.delete()
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
		## iterate all the units
		for u in units:
			## discard all the units with H, S, B, C or no orders
			## they will not move
			try:
				u.order
			except:
				continue
			else:
				if u.order.code in ['H', 'S', 'B', 'C']:
					continue
				else:
					info += u"%s was ordered: %s.\n" % (u, u.order)
			##################
			s = u.strength
			info += u"Supported by = %s.\n" % s
			## rivals and defender are the units trying to enter into or stay
			## in the same area as 'u'
			rivals = u.order.get_rivals()
			defender = u.order.get_defender()
			info += u"Unit has %s rivals.\n" % len(rivals)
			conflict_area = u.get_attacked_area()
			## check if the conflict area is reachable
			if u.order.code == '-':
				if not (u.area.board_area.is_adjacent(conflict_area.board_area,
										fleet=(u.type=='F')) or \
										u.order.find_convoy_line()):
					info += u"Trying to enter an unreachable area.\n"
					u.delete_order()
					continue
			if conflict_area.standoff:
				info += u"Trying to enter a standoff area.\n"
				u.delete_order()
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
							if u.order.code == '-':
								info += u"%s might get empty.\n" % u.area
								conditioned_origins.append(u.area)
							elif u.order.code == '=':
								inv.conversion = u.order.type
							conditioned_invasions.append(inv)
					## if the defender is weaker, the area is invaded and the
					## defender must retreat
					else:
						defender.must_retreat = u.area.board_area.code
						defender.save()
						if u.order.code == '-':
							u.invade_area(defender.area)
							info += u"Invading %s.\n" % defender.area
						elif u.order.code == '=':
							info += u"Converting into %s.\n" % u.order.type
							u.convert(u.order.type)
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
						if u.order.code == '-':
							info += u"Invading %s.\n" % conflict_area
							u.invade_area(conflict_area)
						elif u.order.code == '=':
							info += u"Converting into %s.\n" % u.order.type
							u.convert(u.order.type)
					else:
						## if the area is not empty, and the unit in province
						## is not a friend, and the attacker has supports
						## it invades the area, and the unit in the province
						## must retreat (if it invades another area, it mustnt).
						if unit_leaving.player != u.player and u.strength > 0:
							info += u"There is a unit in %s, but attacker is supported.\n" % conflict_area
							unit_leaving.must_retreat = u.area.board_area.code
							unit_leaving.save()
							if u.order.code == '-':
								u.invade_area(unit_leaving.area)
								info += u"Invading %s.\n" % unit_leaving.area
							elif u.order.code == '=':
								info += u"Converting into %s.\n" % u.order.type
								u.convert(u.order.type)
						## if the area is not empty, the invasion is conditioned
						else:
							info += u"Area is not empty and attacker isn't supported, or there is a friend\n"
							info += u"%s movement is conditioned.\n" % u
							inv = Invasion(u, conflict_area)
							if u.order.code == '-':
								info += u"%s might get empty.\n" % u.area
								conditioned_origins.append(u.area)
							elif u.order.code == '=':
								inv.conversion = u.order.type
							conditioned_invasions.append(inv)
				#u.delete_order()
		for u in units:
			u.delete_order()
		##
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
			try:
				defender = Unit.objects.get(player__game=self,
										type__exact='G',
										area=b.area)
			except:
				info += u"Besieging an empty city. Ignoring.\n"
				b.besieging = False
				b.save()
				continue
			else:
				if b.besieging:
					info += u"for second time.\n"
					b.besieging = False
					info += u"Siege is successful. Garrison disbanded.\n"
					if signals:
						signals.unit_surrendered.send(sender=defender)
					else:
						self.log_event(UnitEvent, type=defender.type,
												area=defender.area.board_area,
												message=2)
					defender.delete()
					b.save()
				else:
					info += u"for first time.\n"
					b.besieging = True
					if signals:
						signals.siege_started.send(sender=b)
					else:
						self.log_event(UnitEvent, type=b.type, area=b.area.board_area, message=3)
					b.save()
			b.order.delete()
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
			if p.number_of_cities() >= self.scenario.cities_to_win:
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
					new_unit = Unit(type=s.unit_type, area=a, player=self)
					new_unit.save()
	
	def number_of_cities(self):
		""" Returns the number of cities controlled by the player. """

		cities = GameArea.objects.filter(player=self, board_area__has_city=True)
		return len(cities)

	def number_of_units(self):
		return self.unit_set.all().count()
	
	def units_to_place(self):
		""" Return the number of units that the player must place. Negative if
		the player has to remove units.
		"""

		if not self.user:
			return 0
		cities = self.number_of_cities()
		if self.game.configuration.disasters:
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
		return self.controlled_home_country().filter(board_area__has_city=True)

	def get_areas_for_new_units(self):
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
		areas = areas.exclude(id__in=excludes)
		return areas

	def check_eliminated(self):
		""" Before updating controls, check if the player is eliminated.

		A player will be eliminated, **unless**:
		- He has at least one empty **and** controlled home city, **OR**
		- One of his home cities is occupied **only** by him.
		"""

		if not self.user:
			return False
		## find a home city controlled by the player, and empty
		cities = self.home_country().filter(player=self,
										unit__isnull=True).count()
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
		

	def deprecated_check_eliminated(self):
		""" If the player has lost all his home cities, eliminates him and disbands
		all his units. Also deletes a possible revolution, and his control flags.

		If excommunication rule is being used, clear excommunications.
		.. Warning::
			This only should be used while there's only one country that can excommunicate.
		"""

		if self.user:
			if len(self.controlled_home_cities()) <= 0:
				self.eliminated = True
				self.save()
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
		return self.eliminated

	def set_conqueror(self, player):
		if player != self:
			signals.country_conquered.send(sender=self, country=self.country)
			self.conqueror = player
			self.save()

	def can_excommunicate(self):
		""" Returns true if player.country.can_excommunicate and nobody has been
		excommunicated this year.
		"""

		if self.eliminated:
			return False
		if self.game.configuration.excommunication:
			if self.country and self.country.can_excommunicate:
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

	def end_phase(self, forced=False):
		self.done = True
		self.save()
		if not forced:
			if self.game.check_bonus_time():
				## get a karma bonus
				#self.user.stats.adjust_karma(1)
				self.user.get_profile().adjust_karma(1)
			## delete possible revolutions
			Revolution.objects.filter(government=self).delete()
		else:
			self.force_phase_change()
		self.game.check_next_phase()

	def new_phase(self):
		## check that the player is not autonomous and is not eliminated
		if self.user and not self.eliminated:
			if self.game.phase == PHREINFORCE:
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
		
		karma = float(self.user.get_profile().karma)
		if karma <= 100:
			time_limit = self.game.time_limit * karma / 100
		else:
			time_limit = self.game.time_limit * (1 + (karma - 100)/200)
		duration = timedelta(0, time_limit)

		return self.game.last_phase_change + duration
	
	def time_exceeded(self):
		""" Returns true if the player has exceeded his own time, and he is playing because
		other players have not yet finished. """

		return self.next_phase_change() < datetime.now()

	def force_phase_change(self):
		## the player didn't take his actions, so he loses karma
		#self.user.stats.adjust_karma(-10)
		self.user.get_profile().adjust_karma(-10)
		## if there is a revolution with an overthrowing player, change users
		try:
			rev = Revolution.objects.get(government=self)
		except ObjectDoesNotExist:
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
					notification.send(user, "got_player", extra_context, on_site=True)
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
				#self.user.stats.adjust_karma(10)
				self.user.get_profile().adjust_karma(10)

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
		try:
			u.order
		except:
			query &= Q(subcode__exact='H')
		else:
			if u.order.code in ('', 'H', 'S', 'C', 'B'): #unit is holding
				query &= Q(subcode__exact='H')
			elif u.order.code == '=':
				query &= Q(subcode__exact='=',
						   subtype=u.order.type)
			elif u.order.code == '-':
				query &= Q(subcode__exact='-',
						   subdestination=u.order.destination)
		support = Order.objects.filter(query).count()
		u.strength = support
		return u

	def list_with_strength(self, game):
		from django.db import connection
		cursor = connection.cursor()
		cursor.execute("SELECT u.id, u.type, u.area_id, u.player_id, u.besieging, u.must_retreat, \
		o.code, o.destination_id, o.type \
		FROM (machiavelli_player p INNER JOIN machiavelli_unit u on p.id=u.player_id) \
		LEFT JOIN machiavelli_order o ON u.id=o.unit_id \
		WHERE p.game_id=%s" % game.id)
		result_list = []
		for row in cursor.fetchall():
			support_query = Q(unit__player__game=game,
							  code__exact='S',
							  subunit__pk=row[0])
			if row[6] in (None, '', 'H', 'S', 'C', 'B'): #unit is holding
				support_query &= Q(subcode__exact='H')
			elif row[6] == '=':
				support_query &= Q(subcode__exact='=',
						   		subtype__exact=row[8])
			elif row[6] == '-':
				support_query &= Q(subcode__exact='-',
								subdestination__pk__exact=row[7])
			support = Order.objects.filter(support_query).count()
			unit = self.model(id=row[0], type=row[1], area_id=row[2],
							player_id=row[3], besieging=row[4],
							must_retreat=row[5])
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
	objects = UnitManager()

	def get_attacked_area(self):
		""" If the unit has orders, get the attacked area, if any. This method is
		only a proxy of the Order method with the same name.
		"""

		try:
			self.order
		except:
			return GameArea.objects.none()
		else:
			return self.order.get_attacked_area()

	def supportable_order(self):
		supportable = "%s %s" % (self.type, self.area.board_area.code)
		try:
			self.order
		except:
			supportable += " H"
		else:
			if self.order.code in ('', 'H', 'S', 'C', 'B'): #unit is holding
				supportable += " H"
			elif self.order.code == '=':
				supportable += " = %s" % self.order.type
			elif self.order.code == '-':
				supportable += " - %s" % self.order.destination.board_area.code
		return supportable

	def place(self):
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
		## and if no garrison exited the city
		if self.area.board_area.is_fortified:
			if self.type == 'A' or (self.type == 'F' and self.area.board_area.has_port):
				if self.must_retreat != self.area.board_area.code:
					try:
						Unit.objects.get(area=self.area, type='G')
					except:
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

	def delete_order(self):
		try:
			self.order.delete()
		except ObjectDoesNotExist:
			pass
		return True

class Order(models.Model):
	""" This class defines an order from a player to a unit. The order will not be
	effective unless it is confirmed.
	"""

	unit = models.OneToOneField(Unit)
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

class Letter(models.Model):
	""" Defines a message sent from a player to another player in the same game. """

	sender = models.ForeignKey(Player, related_name='sent')
	receiver = models.ForeignKey(Player, related_name='received')
	body = models.TextField()
	read = models.BooleanField(default=0)

	def get_style(self, box):
		if box == 'inbox':
			style = "%(country)s" % {'country': self.sender.country.css_class}
		else:
			style = "%(country)s" % {'country': self.receiver.country.css_class}
		if box == 'inbox' and not self.read:
			style += " unread"
		return style
	
	def __unicode__(self):
		return truncatewords(self.body, 5)

	def inbox_color_output(self):
		return "<li class='%(class)s'>%(body)s</li>" % {'class': self.get_style('inbox'),
										'body': self}

	def outbox_color_output(self):
		return "<li class='%(class)s'>%(body)s</li>" % {'class': self.get_style('outbox'),
										'body': self}

def notify_new_letter(sender, instance, created, **kw):
	if notification and isinstance(instance, Letter) and created:
		user = [instance.receiver.user,]
		extra_context = {'game': instance.receiver.game,
						'letter': instance }
		notification.send(user, "letter_received", extra_context , on_site=False)

models.signals.post_save.connect(notify_new_letter, sender=Letter)

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
	disasters = models.BooleanField(_('natural disasters'), default=False)
	special_units = models.BooleanField(_('special units'), default=False,
					help_text=_('will enable Finances and Bribes'))
	strategic = models.BooleanField(_('strategic movement'), default=False)
	lenders = models.BooleanField(_('money lenders'), default=False,
					help_text=_('will enable Finances'))
	conquering = models.BooleanField(_('conquering'), default=False)

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
