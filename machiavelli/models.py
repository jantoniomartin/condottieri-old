import random
import thread
from datetime import datetime, timedelta

from django.db import models
from django.db.models import permalink, Q, Count
from django.contrib.auth.models import User
import django.forms as forms
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification
else:
	notification = None

from machiavelli.graphics import make_map

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

## standard event types
## must be translated in po file
ETFORCEPHASE="Time is over. Forcing new phase"
ETNEWPHASE="Starting phase: %(phase)s"
ETNEWSEASON="Starting season: %(season)s"
ETSUPPORTBROKEN="Support from %(unit)s in %(area)s is broken"
ETCONVERSION="%(unit)s in %(area)s converts into %(type)s"
ETTIEDCONFLICT="A standoff occurs in %(area)s"
ETINVASION="%(unit)s in %(origin)s invades %(area)s"
ETMUSTRETREAT="%(unit)s in %(area)s must retreat"
ETSURRENDER="%(unit)s in %(area)s surrenders"
ETBESIEGE="%(unit)s in %(area)s is now besieging"
ETDISBANDED="%(unit)s in %(area)s is disbanded"
ETRETREAT="%(unit)s in %(origin)s retreats to %(area)s"
ETCONTROL="%(country)s gets control of %(area)s"
ETREINFORCE="A new %(unit)s is placed in %(area)s"
ETORDER="%(country)s's order: %(order)s"

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

def tweet_new_scenario(sender, instance, created, **kw):
	if tweeter_api and isinstance(instance, Scenario):
		if created == True:
			message = "A new scenario has been created: %s" % instance.title
			tweeter_api.PostUpdate(message)

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
		return "%(name)s (%(code)s)" % {'name': self.name, 'code': self.code}
	
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
		self.log_event(ETFORCEPHASE)
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
				p.new_phase()
		self._next_phase()
		
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
		if self.season == 3:
			self.season = 1
			self.year += 1
		else:
			self.season += 1
		self.log_event(ETNEWSEASON, "season:%s" % self.get_season_display())
		## delete all retreats and standoffs
		Unit.objects.filter(player__game=self).update(must_retreat='')
		GameArea.objects.filter(game=self).update(standoff=False)

	def _next_phase(self):
		if self.phase == PHORDERS:
			self.process_orders()
			self.map_changed()
		elif self.phase == PHRETREATS:
			self.process_retreats()
			if self.season == 3:
				self.update_controls()
				if self.check_winner() == True:
					self.assign_scores()
					self.game_over()
					return
			self.map_changed()
		if self.phase == len(GAME_PHASES) - 1:
			self._next_season()
			if self.season == 1:
				self.phase = PHREINFORCE
			else:
				self.phase = PHORDERS
		else:
			self.phase += 1
		self.log_event(ETNEWPHASE, "phase:%s" % self.get_phase_display())
		self.last_phase_change = datetime.now()
		self.save()
		if self.phase == PHRETREATS:
			Order.objects.filter(unit__player__game=self).delete()
		if self.map_outdated == True:
			print "Map is outdated"
			self.make_map()
    
	def check_next_phase(self):
		"""
When a player ends its phase, send a signal to the game. This function checks
if all the players have finished.
		"""
		for p in self.player_set.all():
			if not p.done:
				return False
		self._next_phase()
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

	def log_event(self, e, params=''):
		"""
Logs and event with a special format that allows it to be translated.
		"""
		#assert isinstance(e, str)
		event = Log(game=self, year=self.year, season=self.season,
					phase=self.phase, event=e, params=params)
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
				self.log_event(ETSUPPORTBROKEN, "unit:%s;area:%s" % (s.unit.type, s.unit.area))
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
				self.log_event(ETCONVERSION, "unit:%s;area:%s;type:%s" % (g.type, g.area, 'G'))
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
				self.log_event(ETTIEDCONFLICT, "area:%s" % u.order.get_attacked_area())
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
							self.log_event(ETINVASION, "unit:%s;origin:%s;area:%s" %
												(u.type, u.area, u.order.destination))
							invasion = u.area.board_area.code
							u.area = u.order.destination
							u.must_retreat = ''
							u.save()
				elif u.order.code == '=':
					if not u.area.standoff:
						self.log_event(ETCONVERSION, "unit:%s;area:%s;type:%s" %
													(u.type, u.area, u.order.type))
						u.type = u.order.type
						u.save()
						invasion = u.area.board_area.code
				if invasion:
					## there could be 1 unit that should leave. this unit is marked to retreat.
					## however, the unit may move if it has a '-' order
					leaving = Unit.objects.filter(area=u.area, type__in=['A','F']).exclude(id=u.id)
					for e in leaving:
						self.log_event(ETMUSTRETREAT, "unit:%s;area:%s" % (u.type, u.area))
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
					self.log_event(ETSURRENDER, "unit:%s;area:%s" % (defender.type, defender.area))
					defender.delete()
					b.save()
			else:
				b.besieging = True
				self.log_event(ETBESIEGE, "unit:%s;area:%s" % (b.type, b.area))
				b.save()
			b.order.delete()
		

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
		self.resolve_conflicts()
		self.resolve_sieges()

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
				self.log_event(ETRETREAT, "unit:%s;origin:%s;area:%s" % (unit.type, unit.area, r))
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
			if len(players) == 1:
				self.log_event(ETCONTROL, "country:%s;area:%s" % (players[0].country, area))
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
		self.log_set.all().delete()
		self.gamearea_set.all().delete()

	def notify_players(self, label, extra_context=None, on_site=True):
		if notification:
			users = User.objects.filter(player__game=self)
			notification.send(users, label, extra_context, on_site)

	def tweet_message(self, message):
		if tweeter_api:
			thread.start_new_thread(tweeter_api.PostUpdate, (message,))
			#tweeter_api.PostUpdate(message)

	def tweet_results(self):
		if tweeter_api:
			winners = self.player_set.order_by('-score')
			message = "'%s' - Winner: %s; 2nd: %s; 3rd: %s" % (self.slug,
							winners[0].user,
							winners[1].user,
							winners[2].user)
			self.tweet_message(message)

def tweet_new_game(sender, instance, created, **kw):
	if tweeter_api and isinstance(instance, Game):
		if created == True:
			message = "New game: %s" % instance.slug
			tweeter_api.PostUpdate(message)

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
		return self.board_area.name

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
			if row[6] in ('', 'H', 'S', 'C'): #unit is holding
				suborder += " H"
			elif row[6] == 'B':
				suborder += " B"
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
		self.player.game.log_event(ETREINFORCE, "unit:%s;area:%s" % (self.type, self.area))
		self.save()

	def delete(self):
		self.player.game.log_event(ETDISBANDED, "unit:%s;area:%s" % (self.type, self.area))
		super(Unit, self).delete()
	
	def __unicode__(self):
		return _("%(type)s in %(area)s") % {'type': self.type, 'area': self.area}
    
class Order(models.Model):
	unit = models.OneToOneField(Unit)
	code = models.CharField(max_length=1, choices=ORDER_CODES)
	destination = models.ForeignKey(GameArea, blank=True, null=True)
	type = models.CharField(max_length=1, blank=True, null=True, choices=UNIT_TYPES)
	suborder = models.CharField(max_length=14, blank=True, null=True)

	def save(self, *args, **kwargs):
		super(Order, self).save(*args, **kwargs)
		self.unit.player.game.log_event(ETORDER, "country:%s;order:%s" % (self.unit.player.country.name, self.format()))
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
										Q(area=self.destination))
										#(Q(order__isnull=True) |
										#Q(order__code__in=['B','H','S','C']))
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

class Log(models.Model):
	game = models.ForeignKey(Game)
	year = models.PositiveIntegerField()
	season = models.PositiveIntegerField(choices=SEASONS)
	phase = models.PositiveIntegerField(choices=GAME_PHASES)
	event = models.CharField(max_length=255)
	params = models.CharField(null=True, blank=True, max_length=255)

	def _get_params_dict(self):
		if self.params == '':
			return {}
		params_dict = {}
		params_list = self.params.split(';')
		for p in params_list:
			k, v = p.split(':')[0:2]
			params_dict[k] = _(v)
		return params_dict

	def __unicode__(self):
		result = "%(season)s %(year)d: " % {'season': self.get_season_display(),
												'year': self.year}
		try:
			result += _(self.event) % self._get_params_dict()
		except:
			return result
		else:
			return result

	def color_output(self):
		return "<li class='season_%(season)s'>%(log)s</li>" % {'season': self.season,
																	'log': self}

class Letter(models.Model):
	sender = models.ForeignKey(Player, related_name='sent')
	receiver = models.ForeignKey(Player, related_name='received')
	body = models.TextField()
	read = models.BooleanField(default=0)

	def get_style(self, box):
		if box == 'inbox':
			style = "%(country)s" % {'country': self.sender.country}
		else:
			style = "%(country)s" % {'country': self.receiver.country}
		if box == 'inbox' and not self.read:
			style += " unread"
		return style
	
	def __unicode__(self):
		return self.body[:20]

	def inbox_color_output(self):
		return "<div class='%(class)s'>%(body)s</div>" % {'class': self.get_style('inbox'),
										'body': self}

	def outbox_color_output(self):
		return "<div class='%(class)s'>%(body)s</div>" % {'class': self.get_style('outbox'),
										'body': self}
