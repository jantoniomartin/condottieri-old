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

## stdlib
import random
import thread
from datetime import datetime, timedelta

## django
from django.db import models
from django.db.models import permalink, Q, Count
from django.contrib.auth.models import User
import django.forms as forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.template.defaultfilters import capfirst, truncatewords

if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None

## machiavelli
from machiavelli.graphics import make_map
from machiavelli.logging import save_snapshot

try:
	settings.TWITTER_USER
except:
	twitter_api = None
else:
	import twitter
	twitter_api = twitter.Api(username=settings.TWITTER_USER,
							  password=settings.TWITTER_PASSWORD)

if settings.TWEET_NEW_USERS:
	def tweet_new_user(sender, instance, created, **kw):
		if twitter_api and isinstance(instance, User):
			if created == True:
				message = "New user: %s" % instance.username
				twitter_api.PostUpdate(message)
	
	models.signals.post_save.connect(tweet_new_user, sender=User)

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

## time limit in seconds for a game phase
TIME_LIMITS = ((5*24*60*60, _('5 days')),
			(4*24*60*60, _('4 days')),
			(3*24*60*60, _('3 days')),
			(2*24*60*60, _('2 days')),
			(24*60*60, _('1 day')),
			(12*60*60, _('1/2 day'))
)

## SCORES
## points assigned to the first, second and third players
SCORES=[20, 10, 5]

class AutoTranslateField(models.CharField):
	"""
This class is a CharField whose contents are translated when shown to the
user. You need an aux file (translate.py) for manage.py to make the messages.
	"""
	__metaclass__ = models.SubfieldBase
	def to_python(self, value):
		return unicode(_(value))

class Scenario(models.Model):
	name = models.CharField(max_length=16, unique=True)
	title = AutoTranslateField(max_length=128)
	start_year = models.PositiveIntegerField()
	cities_to_win = models.PositiveIntegerField(default=15)

	def get_slots(self):
		slots = len(self.setup_set.values('country').distinct()) - 1
		return slots

	def __unicode__(self):
		return self.title

	def get_absolute_url(self):
		return ('scenario-detail', (), {'object_id': self.id})
	get_absolute_url = permalink(get_absolute_url)

if twitter_api and settings.TWEET_NEW_SCENARIO:
	def tweet_new_scenario(sender, instance, created, **kw):
		if twitter_api and isinstance(instance, Scenario):
			if created == True:
				message = "A new scenario has been created: %s" % instance.title
				twitter_api.PostUpdate(message)

	models.signals.post_save.connect(tweet_new_scenario, sender=Scenario)

class Country(models.Model):
    name = AutoTranslateField(max_length=20, unique=True)
    css_class = models.CharField(max_length=20, unique=True)
    
    def __unicode__(self):
        return self.name

class Area(models.Model):
	"""
This model describes *only* the area features in the board. The game is
actually played in GameArea objects
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
		"""
Two areas can be adjacent through land, but not through a coast.
		"""
		only_armies = [
			('AVI', 'PRO'),
			('PISA', 'SIE'),
			('CAP', 'AQU'),
			('NAP', 'AQU'),
			('SAL', 'AQU'),
			('SAL', 'BARI'),
			('HER', 'ALB'),
		]
		if fleet:
			if (self.code, area.code) in only_armies or (area.code, self.code) in only_armies:
				return False
		return area in self.borders.all()

	def accepts_type(self, type):
		"""
Returns True if an given type of Unit can be in the Area
		"""
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
		return "(%(code)s) %(name)s" % {'name': self.name, 'code': self.code}
	
	class Meta:
		ordering = ('code',)


class Setup(models.Model):
	scenario = models.ForeignKey(Scenario)
	country = models.ForeignKey(Country, blank=True, null=True)
	area = models.ForeignKey(Area)
	unit_type = models.CharField(max_length=1, blank=True, choices=UNIT_TYPES)
    
	def __unicode__(self):
		return "%s places a %s in %s (%s)" % (self.country, self.unit_type, self.area, self.scenario)

	class Meta:
		unique_together = (("scenario", "area"),)

class Game(models.Model):
	"""
year, season and field are null when the game is first created and will be
populated when the game is started, from the scenario data.
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

	def next_phase_change(self):
		"""
Returns the Time of the next compulsory phase change.
		"""
		duration = timedelta(0, self.time_limit)
		return self.last_phase_change + duration
	
	def force_phase_change(self):
		"""
When the time limit is reached and one or more of the players are not done,
a phase change is forced.
		"""
		self.notify_players("phase_change_forced", {"game": self})
		for p in self.player_set.all():
			if p.done:
				continue
			else:
				if self.phase == PHREINFORCE:
					reinforce = p.units_to_place()
					if reinforce < 0:
						## delete the newest units
						Unit.objects.filter(player=p).order_by('-id')[:-reinforce].delete()
				elif self.phase == PHORDERS:
					pass
				elif self.phase == PHRETREATS:
					## disband the units that should retreat
					Unit.objects.filter(player=p).exclude(must_retreat__exact='').delete()
				p.end_phase()
		
	def check_time_limit(self):
		"""
Checks if the time limit has been reached
		"""
		if not self.phase == PHINACTIVE:
			limit = self.next_phase_change()
			to_limit = limit - datetime.now()
			if to_limit <= timedelta(0, 0):
				self.force_phase_change()
	
	def get_map_url(self):
		return "map-%s.jpg" % self.id
	
	def get_absolute_url(self):
		return "game/%s" % self.id
	
	def make_map(self):
		#make_map(self)
		thread.start_new_thread(make_map, (self,))
		return True

	def map_changed(self):
		if self.map_outdated == False:
			self.map_outdated = True
			self.save()
	
	def map_saved(self):
		if self.map_outdated == True:
			self.map_outdated = False
			self.save()

	def player_joined(self):
		self.slots -= 1
		#self.map_outdated = True
		if self.slots == 0:
			#the game has all its players and should start
			self.year = self.scenario.start_year
			self.season = 1
			self.phase = PHORDERS
			self.create_game_board()
			self.shuffle_countries()
			self.place_initial_units()
			self.map_outdated = True
			self.last_phase_change = datetime.now()
			self.notify_players("game_started", {"game": self})
		self.save()
		if self.map_outdated == True:
			self.make_map()

	def shuffle_countries(self):
		"""
Assign a Country of the Scenario to each Player
		"""
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
		"""
Creates the GameAreas for the Game
		"""
		for a in Area.objects.all():
			ga = GameArea(game=self, board_area=a)
			ga.save()

	def get_autonomous_setups(self):
		return Setup.objects.filter(scenario=self.scenario,
				country__isnull=True).select_related()
	
	def place_initial_garrisons(self):
		"""
Creates the Autonomous Player, and places the autonomous garrisons at the
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

	def place_initial_units(self):
		for p in self.player_set.filter(user__isnull=False):
			p.place_initial_units()
		self.place_initial_garrisons()
	
	def _next_season(self):
		## take a snapshot of the units layout
		thread.start_new_thread(save_snapshot, (self,))
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
			if self.season == 3:
				self.update_controls()
				if self.check_winner() == True:
					self.assign_scores()
					self.game_over()
					return
			self._next_season()
			if self.season == 1:
				next_phase = PHREINFORCE
			else:
				next_phase = PHORDERS
		self.phase = next_phase
		self.last_phase_change = datetime.now()
		self.map_changed()
		self.save()
		self.make_map()
		self.notify_players("new_phase", {"game": self}, on_site=False)
    
	def check_next_phase(self):
		"""
When a player ends its phase, send a signal to the game. This function checks
if all the players have finished.
		"""
		for p in self.player_set.all():
			if not p.done:
				return False
		self.all_players_done()
		for p in self.player_set.all():
			p.new_phase()

	def __unicode__(self):
		return "%d" % (self.pk)

	def get_conflict_areas(self):
		"""
Return the orders that could result in a possible conflict
these are the advancing units and the units that try to convert into A or F
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

	def deprecated_log_event(self, e, params=''):
		"""
Logs and event with a special format that allows it to be translated.
		"""
		#assert isinstance(e, str)
		event = Log(game=self, year=self.year, season=self.season,
					phase=self.phase, event=e, params=params)
		event.save()

	def log_event(self, e, **kwargs):
		## TODO: CATCH ERRORS
		event = e(game=self, year=self.year, season=self.season, phase=self.phase, **kwargs)
		event.save()

	def filter_supports(self):
		"""
Checks which Units with support orders are being attacked and delete their
orders.
		"""
		support_orders = Order.objects.filter(unit__player__game=self, code__exact='S')
		for s in support_orders:
			if s.unit.area in self.get_conflict_areas():
				attacks = Order.objects.filter((Q(code__exact='-') & Q(destination=s.unit.area)) |
												(Q(code__exact='=') & Q(unit__area=s.unit.area) &
												Q(unit__type__exact='G')))
				if len(attacks) == 1:
					params = s.suborder.split(' ')
					if (params[2] == '-' and params[3] == attacks[0].unit.area.board_area.code) or \
						(params[2] == '=' and params[3] in ['A','F'] and params[1] == attacks[0].unit.area.board_area.code):
						continue
				self.log_event(UnitEvent, type=s.unit.type, area=s.unit.area.board_area, message=0)
				s.delete()
		support_orders = Order.objects.filter(unit__player__game=self, code__exact='S')
		return support_orders

	def filter_convoys(self):
		"""
Check which Units with C orders are being attacked. Check if they are going to
be defeated, and if so, delete the C order. However doesn't resolve the conflict
		"""
		## find units attacking fleets
		sea_attackers = Unit.objects.filter(Q(player__game=self),
											(Q(order__code__exact='-') &
											Q(order__destination__board_area__is_sea=True)) |
											(Q(order__code__exact='=') &
											Q(area__board_area__code__exact='VEN') &
											Q(type__exact='G')))
		for s in sea_attackers:
			try:
				if s.order.code == '-':
					defender = Unit.objects.get(player__game=self,
											area=s.order.destination)
				elif s.order.code == '=' and s.area.board_area.code == 'VEN':
					defender = Unit.objects.get(player__game=self,
												area=s.area,
												type__exact='F')
			except:
				## area is empty
				continue
			else:
				a_strength = Unit.objects.get_with_strength(self, id=s.id).strength
				d_strength = Unit.objects.get_with_strength(self, id=defender.id).strength
				if a_strength > d_strength:
					try:
						defender.order
					except:
						continue
					else:
						if defender.order.code == 'C':
							defender.order.code = 'H'
	
	def filter_unreachable_attacks(self):
		"""
Delete the orders of units trying to go to non-adjacent areas and not having a convoy line.
		"""
		attackers = Order.objects.filter(unit__player__game=self, code__exact='-')
		for o in attackers:
			is_fleet = False
			if o.unit.type == 'F':
				is_fleet = True
			if not o.unit.area.board_area.is_adjacent(o.destination.board_area, is_fleet):
				if is_fleet:
					o.delete()
				else:
					if not o.find_convoy_line():
						o.delete()
	
	def resolve_auto_garrisons(self):
		"""
Units with '= G' orders in areas without a garrison, convert into garrison
		"""
		garrisoning = Unit.objects.filter(player__game=self,
									order__code__exact='=',
									order__type__exact='G')
		for g in garrisoning:
			try:
				defender = Unit.objects.get(player__game=self,
										type__exact='G',
										area=g.area)
			except:
				self.log_event(ConversionEvent, area=g.area.board_area, before=g.type, after='G')
				g.type = 'G'
				g.order.delete()
				g.save()

	def resolve_conflicts(self):
		"""
		Conflict: When two or more units want to occupy the same area. This method takes all the
		units and decides which unit occupies each conflict area and which units must retreat.
		"""
		## units sorted (reverse) by a temporary strength attribute
		units = Unit.objects.list_with_strength(self)
		## iterate the units that have orders of types '-' or '='
		for u in units:
			try:
				u.order
			except:
				continue
			else:
				if u.order.code in ['H', 'S', 'B', 'C']:
					continue
			s = u.strength
			## enemies are the units trying to occupy the same area than 'u'
			enemies = u.order.get_enemies()
			## check if there is a unit with the same strength than 'u'
			## it's impossible to have more strength because of the sorting
			tie = False
			for e in enemies:
				strength = Unit.objects.get_with_strength(self,id=e.id).strength
				if strength == s:
					tie = True
					exit
			## if there is a tie, a standoff occurs, and the area is marked as standoff
			if tie:
				self.log_event(StandoffEvent, area=u.order.get_attacked_area().board_area)
				if u.order.code == '-':
					u.order.destination.standoff = True
					u.order.destination.save()
				elif u.order.code == '=':
					u.area.standoff = True
					u.area.save()
			## if there is no tie, 'u' wins the conflict
			else:
				invasion_from = False
				if u.order.code == '-':
					## a standoff area cannot be invaded
					## if not, and the area is reachable, move the unit, cancel a possible retreat
					if not u.order.destination.standoff:
						if u.area.board_area.is_adjacent(u.order.destination.board_area,
													fleet=(u.type=='F')) or \
													u.order.find_convoy_line():
							self.log_event(MovementEvent, type=u.type,
															origin=u.area.board_area,
															destination=u.order.destination.board_area)
							invasion = u.area.board_area.code
							u.area = u.order.destination
							u.must_retreat = ''
							u.save()
				elif u.order.code == '=':
					if not u.area.standoff:
						self.log_event(ConversionEvent, area=u.area.board_area,
														before=u.type,
														after=u.order.type)
						u.type = u.order.type
						u.save()
						invasion = u.area.board_area.code
				if invasion:
					## there could be 1 unit that should leave. this unit is marked to retreat.
					## however, the unit may move if it has a '-' order
					leaving = Unit.objects.filter(area=u.area, type__in=['A','F']).exclude(id=u.id)
					for e in leaving:
						e.must_retreat = invasion
						e.save()
			u.order.delete()
			## all enemies have their orders deleted, except the ones that want to leave the area
			for e in enemies:
				try:
					if not (e.order.code == '-' and e.area == u.area):
						e.order.delete()
				except:
					continue
	
	def resolve_sieges(self):
		## get besieging units
		besiegers = Unit.objects.filter(player__game=self,
										order__code__exact='B')
		for b in besiegers:
			if b.besieging:
				b.besieging = False
				try:
					defender = Unit.objects.get(player__game=self,
											type__exact='G',
											area=b.area)
				except:
					b.save()
					continue
				else:
					self.log_event(UnitEvent, type=defender.type,
											area=defender.area.board_area,
											message=2)
					defender.delete()
					b.save()
			else:
				b.besieging = True
				self.log_event(UnitEvent, type=b.type, area=b.area.board_area, message=3)
				b.save()
			b.order.delete()
	
	def announce_retreats(self):
		retreating = Unit.objects.filter(player__game=self).exclude(must_retreat__exact='')
		for u in retreating:
			self.log_event(UnitEvent, type=u.type, area=u.area.board_area, message=1)

	def process_orders(self):
		"""
Run a batch of methods in the correct order to process all the orders
		"""
		## H orders were not saved
		## resolve =G that are not opposed
		self.resolve_auto_garrisons()
		## delete supports from units in conflict areas
		self.filter_supports()
		self.filter_convoys()
		self.filter_unreachable_attacks()
		self.resolve_conflicts()
		self.resolve_sieges()
		self.announce_retreats()

	def process_retreats(self):
		"""
From the saved RetreaOrders, process the retreats.
		"""
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
				if unit.area == order.area:
					assert unit.area.board_area.is_fortified == True, "trying to retreat to a non-fortified city"
					unit.type = 'G'
				self.log_event(MovementEvent, type=unit.type,
											origin=unit.area.board_area,
											destination=r.board_area)
				unit.must_retreat = ''
				unit.area = r
				unit.save()
				order.delete()
	
	def update_controls(self):
		"""
Check which GameAreas have been controlled by a Player and update them. 
		"""
		for area in GameArea.objects.filter(Q(game=self) &
								Q(unit__isnull=False) &
								(Q(board_area__is_sea=False) |
								Q(board_area__code__exact='VEN'))).distinct():
			#units = area.unit_set.filter(player__user__isnull=False)
			players = self.player_set.filter(unit__area=area)
			if len(players) == 1 and players[0].user:
				self.log_event(ControlEvent, country=players[0].country, area=area.board_area)
				area.player = players[0]
				area.save()
			elif len(players) == 2:
					area.player = None
					area.save()
			else:
				print "There are more than 2 players in the same area!"
	
	def check_winner(self):
		"""
Returns True if at least one player has reached the cities_to_win
		"""
		for p in self.player_set.filter(user__isnull=False):
			if p.number_of_cities() >= self.scenario.cities_to_win:
				return True
		return False
		
	def assign_scores(self):
		qual = []
		for p in self.player_set.filter(user__isnull=False):
			qual.append((p, p.number_of_cities()))
		## sort the players by their number of cities
		qual.sort(cmp=lambda x,y: cmp(x[1], y[1]), reverse=False)
		for s in SCORES:
			try:
				q = qual.pop()
				q[0].score = s
				q[0].save()
			except:
				exit
			else:
				q[0].score = s
				q[0].save()
				## highest score = last score
				while qual != [] and qual[-1][1] == q[1]:
					tied = qual.pop()
					tied[0].score = s
					tied[0].save()

	def game_over(self):
		self.phase = PHINACTIVE
		self.save()
		self.notify_players("game_over", {"game": self})
		self.tweet_message("The game %(game)s is over" % {'game': self.slug})
		self.clean_useless_data()

	def clean_useless_data(self):
		"""
In a finished game, delete all the data that is not going to be used anymore.
		"""
		try:
			aut = Player.objects.get(game=self, user__isnull=True)
		except:
			print "There should be an autonomous player"
		else:
			aut.delete()
		for p in self.player_set.all():
			p.sent.all().delete()
		self.baseevent_set.all().delete()
		self.gamearea_set.all().delete()

	def notify_players(self, label, extra_context=None, on_site=True):
		if notification:
			users = User.objects.filter(player__game=self)
			notification.send(users, label, extra_context, on_site)

	def tweet_message(self, message):
		if twitter_api:
			thread.start_new_thread(twitter_api.PostUpdate, (message,))
			#twitter_api.PostUpdate(message)

	def tweet_results(self):
		if twitter_api:
			winners = self.player_set.order_by('-score')
			message = "'%s' - Winner: %s; 2nd: %s; 3rd: %s" % (self.slug,
							winners[0].user,
							winners[1].user,
							winners[2].user)
			self.tweet_message(message)

if twitter_api and settings.TWEET_NEW_GAME:
	def tweet_new_game(sender, instance, created, **kw):
		if twitter_api and isinstance(instance, Game):
			if created == True:
				message = "New game: %s" % instance.slug
				twitter_api.PostUpdate(message)

	models.signals.post_save.connect(tweet_new_game, sender=Game)

class GameArea(models.Model):
	game = models.ForeignKey(Game)
	board_area = models.ForeignKey(Area)
	## player is who controls the area, if any
	player = models.ForeignKey('Player', blank=True, null=True)
	standoff = models.BooleanField(default=False)

	def abbr(self):
		return "%s (%s)" % (self.board_area.code, self.board_area.name)

	def __unicode__(self):
		#return self.board_area.name
		return "(%(code)s) %(name)s" % {'name': self.board_area.name, 'code': self.board_area.code}

	def accepts_type(self, type):
		return self.board_area.accepts_type(type)
	
	def possible_reinforcements(self):
		"""
Returns a _list_ of possible unit types for an area
		"""
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

class Player(models.Model):
	user = models.ForeignKey(User, blank=True, null=True) # can be null because of autonomous units
	game = models.ForeignKey(Game)
	country = models.ForeignKey(Country, blank=True, null=True)
	done = models.BooleanField(default=False)
	score = models.PositiveIntegerField(default=0)

	def __unicode__(self):
		if self.user:
			return "%s (%s)" % (self.user, self.game)
		else:
			return "Autonomous in %s" % self.game

	def get_setups(self):
		return Setup.objects.filter(scenario=self.game.scenario,
				country=self.country).select_related()
	
	def place_initial_units(self):
		for s in self.get_setups():
			try:
				a = GameArea.objects.get(game=self.game, board_area=s.area)
			except:
				print "Error 2: Area not found!"
			else:
				a.player = self
				a.save()
				if s.unit_type:
					new_unit = Unit(type=s.unit_type, area=a, player=self)
					new_unit.save()
	
	def number_of_cities(self):
		"""
Return the number of _controlled_ cities
		"""
		cities = GameArea.objects.filter(player=self, board_area__has_city=True)
		return len(cities)

	def units_to_place(self):
		"""
Get the number of units that the player must place. Negative if the player has
to remove units.
		"""
		cities = self.number_of_cities()
		units = len(self.unit_set.all())
		place = cities - units
		slots = len(self.get_areas_for_new_units())
		if place > slots:
			place = slots
		return place
	
	def home_country(self):
		"""
Returns a queryset with Game Areas in home country
		"""
		return GameArea.objects.filter(board_area__setup__scenario=self.game.scenario,
									board_area__setup__country=self.country)

	def controlled_home_country(self):
		"""
Returns a queryset with *Game* Areas in home country controlled by player
		"""
		return self.home_country().filter(player=self)

	def get_areas_for_new_units(self):
		"""
Returns a queryset with the GameAreas that accept new units.
		"""
		##TODO in scenario III of the rules, there are two units in Milan, and this shouldn't
		## be part of a home country. Currently not implemented.
		areas = self.controlled_home_country().filter(board_area__has_city=True)
		excludes = []
		for a in areas:
			if a.board_area.is_fortified and len(a.unit_set.all()) > 1:
				excludes.append(a.id)
			elif not a.board_area.is_fortified and len(a.unit_set.all()) > 0:
				excludes.append(a.id)
		areas = areas.exclude(id__in=excludes)
		return areas

	def end_phase(self):
		self.done = True
		self.save()
		self.game.check_next_phase()

	def new_phase(self):
		if self.user:
			self.done = False
			self.save()

class UnitManager(models.Manager):
	def get_with_strength(self, game, **kwargs):
		u = self.get_query_set().get(**kwargs)
		origin = u.area
		suborder = "%s %s" % (u.type, origin.board_area.code)
		try:
			u.order
		except:
			suborder += " H"
		else:
			if u.order.code in ('', 'H', 'S', 'C'): #unit is holding
				suborder += " H"
			elif u.order.code == 'B':
				suborder += " B"
			elif u.order.code == '=':
				suborder += " = %s" % u.order.type
			elif u.order.code == '-':
				suborder += " - %s" % u.order.destination.board_area.code
		support = Order.objects.filter(unit__player__game=game,
										code__exact='S',
										suborder__exact=suborder).count()
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
			origin = GameArea.objects.get(id=row[2])
			suborder = "%s %s" % (row[1], origin.board_area.code)
			if row[6] in ('', 'H', 'S', 'C', 'B'): #unit is holding
				suborder += " H"
			elif row[6] == '=':
				suborder += " = %s" % row[8]
			elif row[6] == '-':
				destination = GameArea.objects.get(id=row[7])
				suborder += " - %s" % destination.board_area.code
			support = Order.objects.filter(unit__player__game=game,
											code__exact='S',
											suborder__exact=suborder).count()
			unit = self.model(id=row[0], type=row[1], area_id=row[2], player_id=row[3],
							besieging=row[4], must_retreat=row[5])
			unit.strength = support
			result_list.append(unit)
		result_list.sort(cmp=lambda x,y: cmp(x.strength, y.strength), reverse=True)
		return result_list


class Unit(models.Model):
	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	area = models.ForeignKey(GameArea)
	player = models.ForeignKey(Player)
	besieging = models.BooleanField(default=0)
	## must_retreat contains the code, if any, of the area where the attack came from
	must_retreat = models.CharField(max_length=5, blank=True, default='')
	objects = UnitManager()

	def place(self):
		self.player.game.log_event(NewUnitEvent, country=self.player.country, type=self.type, area=self.area.board_area)
		self.save()

	def delete(self):
		self.player.game.log_event(DisbandEvent, country=self.player.country, type=self.type, area=self.area.board_area)
		super(Unit, self).delete()
	
	def __unicode__(self):
		return _("%(type)s in %(area)s") % {'type': self.get_type_display(), 'area': self.area}
    
class Order(models.Model):
	unit = models.OneToOneField(Unit)
	code = models.CharField(max_length=1, choices=ORDER_CODES)
	destination = models.ForeignKey(GameArea, blank=True, null=True)
	type = models.CharField(max_length=1, blank=True, null=True, choices=UNIT_TYPES)
	suborder = models.CharField(max_length=14, blank=True, null=True)

	def suborder_dict(self):
		if self.suborder:
			params = self.suborder.split(" ")
			result = {}
			result['subtype'] = params[0]
			result['suborigin'] = Area.objects.get(code__exact=params[1])
			result['subcode'] = params[2]
			if params[2] == 'H':
				result['subdestination'] = None
				result['subconversion'] = None
			if params[2] == '-':
				result['subdestination'] = Area.objects.get(code__exact=params[3])
				result['subconversion'] = None
			if params[2] == '=':
				result['subdestination'] = None
				result['subconversion'] = params[3]
		else:
			result = {'subtype': None,
					'suborigin': None,
					'subcode': None,
					'subdestination': None,
					'subconversion': None}

		return result

	def save(self, *args, **kwargs):
		super(Order, self).save(*args, **kwargs)
		params = self.suborder_dict()
		if self.destination:
			params['destination'] = self.destination.board_area
		else:
			params['destination'] = None
		self.unit.player.game.log_event(OrderEvent, country=self.unit.player.country,
													type=self.unit.type,
													origin=self.unit.area.board_area,
													code=self.code,
													destination=params['destination'],
													conversion=self.type,
													subtype=params['subtype'],
													suborigin=params['suborigin'],
													subcode=params['subcode'],
													subdestination=params['subdestination'],
													subconversion=params['subconversion'])
		if self.code != 'B':
			self.unit.besieging = False
			self.unit.save()
	
	def format(self):
		"""
Returns a string with the format (as in Machiavelli) of the order.
		"""
		f = "%s %s" % (self.unit.type, self.unit.area.board_area.code)
		f += " %s" % self.code
		if self.code == '-':
			f += " %s" % self.destination.board_area.code
		elif self.code == '=':
			f += " %s" % self.type
		elif self.code == 'S' or self.code == 'C':
			f += " %s" % self.suborder
		return f

	def find_convoy_line(self):
		"""
Returns True if there is a continuous line of convoy orders from the origin
to the destination of the order.
		"""
		origins = [self.unit.area,]
		destination = self.destination
		## get all areas convoying this order AND de destination
		convoy_areas = GameArea.objects.filter((Q(game=self.unit.player.game) &
									Q(board_area__is_sea=True) &
									Q(unit__order__code__exact='C') &
									Q(unit__order__suborder__exact=self.format())) |
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
		"""
Returns a Queryset with all the units trying to oppose an advance or conversion
order.
		"""
		if self.code == '-':
			enemies = Unit.objects.filter(Q(player__game=self.unit.player.game),
										## trying to go to the same area
										Q(order__destination=self.destination) |
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
	
	def get_attacked_area(self):
		if self.code == '-':
			return self.destination
		elif self.code == '=':
			return self.unit.area
		else:
			return GameArea.objects.none()
	
	def __unicode__(self):
		return self.format()

class RetreatOrder(models.Model):
	unit = models.ForeignKey(Unit)
	area = models.ForeignKey(GameArea, null=True, blank=True)

	def __unicode__(self):
		return "%s" % self.unit

class ControlToken(models.Model):
	area = models.OneToOneField(Area)
	x = models.PositiveIntegerField()
	y = models.PositiveIntegerField()

	def __unicode__(self):
		return "%s, %s" % (self.x, self.y)


class GToken(models.Model):
	area = models.OneToOneField(Area)
	x = models.PositiveIntegerField()
	y = models.PositiveIntegerField()

	def __unicode__(self):
		return "%s, %s" % (self.x, self.y)


class AFToken(models.Model):
	area = models.OneToOneField(Area)
	x = models.PositiveIntegerField()
	y = models.PositiveIntegerField()

	def __unicode__(self):
		return "%s, %s" % (self.x, self.y)

class BaseEvent(models.Model):
	game = models.ForeignKey(Game)
	year = models.PositiveIntegerField()
	season = models.PositiveIntegerField(choices=SEASONS)
	phase = models.PositiveIntegerField(choices=GAME_PHASES)
	
	def unit_string(self, type, area):
		if type == 'A':
			return _("the army in %s") % area.name
		elif type == 'F':
			return _("the fleet in %s") % area.name
		elif type == 'G':
			return _("the garrison in %s") % area.name

	def color_output(self):
		try:
			self.newunitevent
		except:
			pass
		else:
			return "<li class=\"%(class)s\">%(log)s</li>" % {'class': self.newunitevent.css_class(),
																	'log': capfirst(self)}
		try:
			self.disbandevent
		except:
			pass
		else:
			return "<li class=\"%(class)s\">%(log)s</li>" % {'class': self.disbandevent.css_class(),
																	'log': capfirst(self)}
		try:
			self.orderevent
		except:
			pass
		else:
			return "<li class=\"%(class)s\">%(log)s</li>" % {'class': self.orderevent.css_class(),
																	'log': capfirst(self)}
		try:
			self.standoffevent
		except:
			pass
		else:
			return "<li class=\"%(class)s\">%(log)s</li>" % {'class': self.standoffevent.css_class(),
																	'log': capfirst(self)}
		try:
			self.conversionevent
		except:
			pass
		else:
			return "<li class=\"%(class)s\">%(log)s</li>" % {'class': self.conversionevent.css_class(),
																	'log': capfirst(self)}
		try:
			self.controlevent
		except:
			pass
		else:
			return "<li class=\"%(class)s\">%(log)s</li>" % {'class': self.controlevent.css_class(),
																	'log': capfirst(self)}
		try:
			self.movementevent
		except:
			pass
		else:
			return "<li class=\"%(class)s\">%(log)s</li>" % {'class': self.movementevent.css_class(),
																	'log': capfirst(self)}
		try:
			self.unitevent
		except:
			return "Unknown event!!??"
		else:
			return "<li class=\"%(class)s\">%(log)s</li>" % {'class': self.unitevent.css_class(),
																	'log': capfirst(self)}

	def __unicode__(self):
		try:
			self.newunitevent
		except:
			pass
		else:
			return unicode(self.newunitevent)
		try:
			self.disbandevent
		except:
			pass
		else:
			return unicode(self.disbandevent)
		try:
			self.orderevent
		except:
			pass
		else:
			return unicode(self.orderevent)
		try:
			self.standoffevent
		except:
			pass
		else:
			return unicode(self.standoffevent)
		try:
			self.conversionevent
		except:
			pass
		else:
			return unicode(self.conversionevent)
		try:
			self.controlevent
		except:
			pass
		else:
			return unicode(self.controlevent)
		try:
			self.movementevent
		except:
			pass
		else:
			return unicode(self.movementevent)
		try:
			self.unitevent
		except:
			return "Unknown event!!??"
		else:
			return unicode(self.unitevent)
	
	class Meta:
		abstract = False
		ordering = ['year', 'season', 'phase']

class NewUnitEvent(BaseEvent):
	country = models.ForeignKey(Country)
	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	area = models.ForeignKey(Area)

	def css_class(self):
		return "season_%(season)s new-unit-event" % {'season': self.season }

	def __unicode__(self):
		return _("%(country)s recruits a new %(type)s in %(area)s.") % {'country': self.country,
																	'type': self.get_type_display(),
																	'area': self.area.name}

class DisbandEvent(BaseEvent):
	country = models.ForeignKey(Country, blank=True, null=True)
	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	area = models.ForeignKey(Area)

	def css_class(self):
		return "season_%(season)s disband-event" % {'season': self.season }

	def __unicode__(self):
		if self.country:
			return _("%(country)s's %(type)s in %(area)s is disbanded.") % {'country': self.country,
																	'type': self.get_type_display(),
																	'area': self.area.name}
		else:
			return _("Autonomous %(type)s in %(area)s is disbanded.") % {
															'type': self.get_type_display(),
															'area': self.area.name}
			

class OrderEvent(BaseEvent):
	country = models.ForeignKey(Country)
	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	origin = models.ForeignKey(Area, related_name='event_origin')
	code = models.CharField(max_length=1, choices=ORDER_CODES)
	destination = models.ForeignKey(Area, blank=True, null=True, related_name='event_destination')
	conversion = models.CharField(max_length=1, choices=UNIT_TYPES, blank=True, null=True)
	subtype = models.CharField(max_length=1, choices=UNIT_TYPES, blank=True, null=True)
	suborigin = models.ForeignKey(Area, related_name='event_suborigin', blank=True, null=True)
	subcode = models.CharField(max_length=1, choices=ORDER_CODES, blank=True, null=True)
	subdestination = models.ForeignKey(Area, blank=True, null=True, related_name='event_subdestination')
	subconversion = models.CharField(max_length=1, choices=UNIT_TYPES, blank=True, null=True)

	def css_class(self):
		return "season_%(season)s order-event" % {'season': self.season }

	def __unicode__(self):
		unit = self.unit_string(self.type, self.origin)
		if self.code == '-':
			return _("%(unit)s tries to go to %(area)s.") % {'unit': unit,
															'area': self.destination.name}
		elif self.code == 'B':
			return _("%(unit)s besieges the city.") % {'unit': unit}
		elif self.code == '=':
			return _("%(unit)s tries to convert into %(type)s.") % {'unit': unit,
																'type': self.get_conversion_display()}
		elif self.code == 'C':
			return _("%(unit)s must convoy %(subunit)s to %(area)s.") % {'unit': unit,
														'subunit': self.unit_string(self.subtype,
																				self.suborigin),
														'area': self.subdestination.name}
		elif self.code == 'S':
			if self.subcode == 'H':
				return _("%(unit)s supports %(subunit)s to hold its position.") % {
														'unit': unit,
														'subunit': self.unit_string(self.subtype,
																				self.suborigin)}
			elif self.subcode == '-':
				return _("%(unit)s supports %(subunit)s to go to %(area)s.") % {
														'unit': unit,
														'subunit': self.unit_string(self.subtype,
																				self.suborigin),
														'area': self.subdestination.name}
			elif self.subcode == '=':
				return _("%(unit)s supports %(subunit)s to convert into %(type)s.") % {
														'unit': unit,
														'subunit': self.unit_string(self.subtype,
																				self.suborigin),
														'type': self.get_subconversion_display()}

class StandoffEvent(BaseEvent):
	area = models.ForeignKey(Area)

	def css_class(self):
		return "season_%(season)s standoff-event" % {'season': self.season }

	def __unicode__(self):
		return _("Conflicts in %(area)s result in a standoff.") % {'area': self.area.name}

class ConversionEvent(BaseEvent):
	area = models.ForeignKey(Area)
	before = models.CharField(max_length=1, choices=UNIT_TYPES)
	after = models.CharField(max_length=1, choices=UNIT_TYPES)

	def css_class(self):
		return "season_%(season)s conversion-event" % {'season': self.season }

	def __unicode__(self):
		return _("%(unit)s converts into %(type)s.") % {'unit': self.unit_string(self.before, self.area),
														'type': self.get_after_display()}

class ControlEvent(BaseEvent):
	country = models.ForeignKey(Country)
	area = models.ForeignKey(Area)

	def css_class(self):
		return "season_%(season)s control-event" % {'season': self.season }

	def __unicode__(self):
		return _("%(country)s gets control of %(area)s.") % {'country': self.country,
															'area': self.area.name }

class MovementEvent(BaseEvent):
	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	origin = models.ForeignKey(Area, related_name="origin")
	destination = models.ForeignKey(Area, related_name="destination")

	def css_class(self):
		return "season_%(season)s movement-event" % {'season': self.season }

	def __unicode__(self):
		if self.phase == PHORDERS:
			return _("%(unit)s advances into %(destination)s.") % {'unit': self.unit_string(self.type,
																						self.origin),
																'destination': self.destination.name}
		elif self.phase == PHRETREATS:
			return _("%(unit)s tries to retreat to %(destination)s.") % {'unit': self.unit_string(self.type,
																						self.origin),
																'destination': self.destination.name}

EVENT_MESSAGES = (
	(0, _('cannot carry out its support order.')),
	(1, _('must retreat.')),
	(2, _('surrenders.')),
	(3, _('is now besieging.'))
)

class UnitEvent(BaseEvent):
	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	area = models.ForeignKey(Area)
	message = models.PositiveIntegerField(choices=EVENT_MESSAGES)
	
	def css_class(self):
		if self.message == 0:
			e = 'broken-support-event'
		elif self.message == 1:
			e = 'retreat-event'
		elif self.message == 2:
			e = 'surrender-event'
		elif self.message == 3:
			e = 'besieging-event'
		return "season_%(season)s %(event)s" % {'season': self.season, 'event': e }

	def __unicode__(self):
		return "%(unit)s %(message)s" % {'unit': self.unit_string(self.type, self.area),
										'message': self.get_message_display()}

class Letter(models.Model):
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
