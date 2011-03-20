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

""" This application manages the log of events during a Condottieri game.

"""

## django
from django.db import models
from django.utils.translation import ugettext_lazy as _

## machiavelli
from machiavelli.models import *
from machiavelli.signals import *

if "jogging" in settings.INSTALLED_APPS:
	from jogging import logging
else:
	logging = None


class BaseEvent(models.Model):
	"""
BaseEvent is the parent class for all kind of game events.
	"""
	game = models.ForeignKey(Game)
	year = models.PositiveIntegerField()
	season = models.PositiveIntegerField(choices=SEASONS)
	phase = models.PositiveIntegerField(choices=GAME_PHASES)
	classname = models.CharField(max_length=32, editable=False)
	
	def get_concrete(self):
		""" Gets the name of the child class of this BaseEvent """
		return self.__getattribute__(self.classname.lower())

	def unit_string(self, type, area):
		""" Returns a string like **the garrison in Naples** """
		if type == 'A':
			return _("the army in %s") % area.name
		elif type == 'F':
			return _("the fleet in %s") % area.name
		elif type == 'G':
			return _("the garrison in %s") % area.name

	def season_class(self):
		""" Returns a css class name for the game season """
		return "season_%s" % self.season

	def event_class(self):
		""" Returns a css class name depending on the type of event """
		return self.get_concrete().event_class()
	
	def color_output(self):
		""" Returns a html list item with season and event styles """
		return "<li class=\"%(season_class)s %(event_class)s\">%(log)s</li>" % {
							'season_class': self.season_class(),
							'event_class': self.event_class(),
							'log': capfirst(self)
							}

	def __unicode__(self):
		return unicode(self.get_concrete())
	
	class Meta:
		abstract = False
		ordering = ['-year', '-season', '-id']

def log_event(event_class, game, **kwargs):
	""" Creates a new BaseEvent and its child event. """
	try:
		event = event_class(game=game, year=game.year, season=game.season, phase=game.phase, **kwargs)
		event.save()
	except:
		if logging:
			logging.info("Error in log_event")

class NewUnitEvent(BaseEvent):
	""" Event triggered when a new unit is placed in the map. """

	country = models.ForeignKey(Country)
	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	area = models.ForeignKey(Area)
	
	def event_class(self):
		return "new-unit-event"

	def __unicode__(self):
		return _("%(country)s recruits a new %(type)s in %(area)s.") % {
						'country': self.country,
						'type': self.get_type_display(),
						'area': self.area.name
						}

def log_new_unit(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(NewUnitEvent, sender.player.game,
					classname="NewUnitEvent",
					country=sender.player.country,
					type=sender.type,
					area=sender.area.board_area)

unit_placed.connect(log_new_unit)

class DisbandEvent(BaseEvent):
	""" Event triggered when a unit is disbanded. """
	country = models.ForeignKey(Country, blank=True, null=True)
	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	area = models.ForeignKey(Area)

	def event_class(self):
		return "disband-event"

	def __unicode__(self):
		if self.country:
			return _("%(country)s's %(type)s in %(area)s is disbanded.") % {
						'country': self.country,
						'type': self.get_type_display(),
						'area': self.area.name
						}
		else:
			return _("Autonomous %(type)s in %(area)s is disbanded.") % {
						'type': self.get_type_display(),
						'area': self.area.name}
			
def log_disband(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(DisbandEvent, sender.player.game,
					classname="DisbandEvent",
					country=sender.player.country,
					type=sender.type,
					area=sender.area.board_area)

unit_disbanded.connect(log_disband)

class OrderEvent(BaseEvent):
	""" Event triggered when an order is confirmed. """
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

	def event_class(self):
		return "order-event"

	def __unicode__(self):
		country_info = "<small>(%s)</small>" % (unicode(self.country),)
		msg = self.get_message()
		return "%s %s" % (country_info, msg)
	
	def get_message(self):
		unit = self.unit_string(self.type, self.origin)
		if self.code == '-':
			msg = _("%(unit)s tries to go to %(area)s.") % {
							'unit': unit,
							'area': self.destination.name
							}
		elif self.code == 'B':
			msg = _("%(unit)s besieges the city.") % {'unit': unit}
		elif self.code == '=':
			msg = _("%(unit)s tries to convert into %(type)s.") % {
							'unit': unit,
							'type': self.get_conversion_display()
							}
		elif self.code == 'C':
			msg = _("%(unit)s must convoy %(subunit)s to %(area)s.") % {
							'unit': unit,
							'subunit': self.unit_string(self.subtype,
														self.suborigin),
							'area': self.subdestination.name
							}
		elif self.code == 'S':
			if self.subcode == 'H':
				msg=_("%(unit)s supports %(subunit)s to hold its position.") % {
							'unit': unit,
							'subunit': self.unit_string(self.subtype,
														self.suborigin)
							}
			elif self.subcode == '-':
				msg = _("%(unit)s supports %(subunit)s to go to %(area)s.") % {
							'unit': unit,
							'subunit': self.unit_string(self.subtype,
														self.suborigin),
							'area': self.subdestination.name
							}
			elif self.subcode == '=':
				msg = _("%(unit)s supports %(subunit)s to convert into %(type)s.") % {
							'unit': unit,
							'subunit': self.unit_string(self.subtype,
														self.suborigin),
							'type': self.get_subconversion_display()
							}
		return msg

def log_order(sender, **kwargs):
	assert isinstance(sender, Order), "sender must be an Order"
	try:
		destination = sender.destination.board_area
	except:
		destination = None
	if isinstance(sender.subunit, Unit):
		subtype = sender.subunit.type
		suborigin = sender.subunit.area.board_area
	else:
		subtype = None
		suborigin = None
	try:
		subdestination = sender.subdestination.board_area
	except:
		subdestination = None
	log_event(OrderEvent, sender.unit.player.game,
					classname="OrderEvent",
					country = sender.player.country,
					type = sender.unit.type,
					origin = sender.unit.area.board_area,
					code = sender.code,
					destination = destination,
					conversion = sender.type,
					subtype = subtype,
					suborigin = suborigin,
					subcode = sender.subcode,
					subdestination = subdestination,
					subconversion = sender.subtype)

order_placed.connect(log_order)

class StandoffEvent(BaseEvent):
	""" Event triggered when a standoff happens. """
	area = models.ForeignKey(Area)

	def event_class(self):
		return "standoff-event"

	def __unicode__(self):
		return _("Conflicts in %(area)s result in a standoff.") % {
						'area': self.area.name,
						}

def log_standoff(sender, **kwargs):
	assert isinstance(sender, GameArea), "sender must be a GameArea"
	log_event(StandoffEvent, sender.game,
					classname="StandoffEvent",
					area = sender.board_area)

standoff_happened.connect(log_standoff)

class ConversionEvent(BaseEvent):
	""" Event triggered when a unit changes its type. """

	area = models.ForeignKey(Area)
	before = models.CharField(max_length=1, choices=UNIT_TYPES)
	after = models.CharField(max_length=1, choices=UNIT_TYPES)

	def event_class(self):
		return "conversion-event"

	def __unicode__(self):
		return _("%(unit)s converts into %(type)s.") % {
						'unit': self.unit_string(self.before, self.area),
						'type': self.get_after_display()
						}

def log_conversion(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(ConversionEvent, sender.player.game,
					classname="ConversionEvent",
					area=sender.area.board_area,
					before=kwargs["before"],
					after=kwargs["after"])

unit_converted.connect(log_conversion)

class ControlEvent(BaseEvent):
	""" Event triggered when a player gets the control of a province. """
	country = models.ForeignKey(Country)
	area = models.ForeignKey(Area)

	def event_class(self):
		return "control-event"

	def __unicode__(self):
		return _("%(country)s gets control of %(area)s.") % {
						'country': self.country,
						'area': self.area.name
						}

def log_control(sender, **kwargs):
	assert isinstance(sender, GameArea), "sender must be a GameArea"
	log_event(ControlEvent, sender.player.game,
					classname="ControlEvent",
					country=sender.player.country,
					area=sender.board_area)

area_controlled.connect(log_control)

class MovementEvent(BaseEvent):
	""" Event triggered when a unit moves to a different province. """

	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	origin = models.ForeignKey(Area, related_name="movement_origin")
	destination = models.ForeignKey(Area, related_name="movement_destination")

	def event_class(self):
		return "movement-event"

	def __unicode__(self):
		return _("%(unit)s advances into %(destination)s.") % {
				'unit': self.unit_string(self.type,	self.origin),
				'destination': self.destination.name
				}

def log_movement(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(MovementEvent, sender.player.game,
					classname="MovementEvent",
					type=sender.type,
					origin=sender.area.board_area,
					destination=kwargs['destination'].board_area)

unit_moved.connect(log_movement)

class RetreatEvent(BaseEvent):
	""" Event triggered when a unit retreats. """

	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	origin = models.ForeignKey(Area, related_name="retreat_origin")
	destination = models.ForeignKey(Area, related_name="retreat_destination")

	def event_class(self):
		return "movement-event"

	def __unicode__(self):
		if self.origin == self.destination:
			return _("%(unit)s garrisons in the city.") % {
					'unit': self.unit_string(self.type,	self.origin),
					'destination': self.destination.name
					}
		else:
			return _("%(unit)s retreats to %(destination)s.") % {
					'unit': self.unit_string(self.type,	self.origin),
					'destination': self.destination.name
					}

def log_retreat(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(RetreatEvent, sender.player.game,
					classname="RetreatEvent",
					type=sender.type,
					origin=sender.area.board_area,
					destination=kwargs['destination'].board_area)

unit_retreated.connect(log_retreat)

UNIT_EVENTS = (
	(0, _('cannot carry out its support order.')),
	(1, _('must retreat.')),
	(2, _('surrenders.')),
	(3, _('is now besieging.'))
)

class UnitEvent(BaseEvent):
	""" Event triggered when a unit is subject to some conditions.

	Currently, the conditions are:
	
	* The unit cannot carry out its support order.
	
	* The unit must retreat.
	
	* The unit surrenders (because of a siege).
	
	* The unit starts a siege.
	
	Each condition must have its own signal.
	"""

	type = models.CharField(max_length=1, choices=UNIT_TYPES)
	area = models.ForeignKey(Area)
	message = models.PositiveIntegerField(choices=UNIT_EVENTS)
	
	def event_class(self):
		if self.message == 0:
			return 'broken-support-event'
		elif self.message == 1:
			return 'retreat-event'
		elif self.message == 2:
			return 'surrender-event'
		elif self.message == 3:
			return 'besieging-event'

	def __unicode__(self):
		return "%(unit)s %(message)s" % {
						'unit': self.unit_string(self.type, self.area),
						'message': self.get_message_display()
						}

def log_broken_support(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(UnitEvent, sender.player.game,
					classname="UnitEvent",
					type=sender.type,
					area=sender.area.board_area,
					message=0)

support_broken.connect(log_broken_support)

def log_forced_retreat(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(UnitEvent, sender.player.game,
				classname="UnitEvent",
				type=sender.type,
				area=sender.area.board_area,
				message=1)

forced_to_retreat.connect(log_forced_retreat)

def log_unit_surrender(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(UnitEvent, sender.player.game,
				classname="UnitEvent",
				type=sender.type,
				area=sender.area.board_area,
				message=2)

unit_surrendered.connect(log_unit_surrender)

def log_siege_start(sender, **kwargs):
	assert isinstance(sender, Unit), "sender must be a Unit"
	log_event(UnitEvent, sender.player.game,
				classname="UnitEvent",
				type=sender.type,
				area=sender.area.board_area,
				message=3)

siege_started.connect(log_siege_start)
	
COUNTRY_EVENTS = (
	(0, _('Government has been overthrown')),
	(1, _('Has been conquered')),
	(2, _('Has been declared enemy of Christendom')),
	(3, _('Has been eliminated')),
)

class CountryEvent(BaseEvent):
	""" Event triggered when a country is subject to some conditions.

	Currently, the conditions are:
	
	* A new player (not playing) takes the control of the country.
	
	* The country has been conquered.
	
	* The country has been excommunicated.

	* The country has been eliminated.
	
	Each condition must have its own signal.
	"""
	country = models.ForeignKey(Country)
	message = models.PositiveIntegerField(choices=COUNTRY_EVENTS)

	def __unicode__(self):
		return "%(country)s: %(message)s" % {
									'country': self.country.name,
									'message': self.get_message_display()
									}
	
	def event_class(self):
		return "season_%(season)s" % {'season': self.season}

def log_overthrow(sender, **kwargs):
	assert isinstance(sender, Player), "sender must be a Player"
	log_event(CountryEvent, sender.game,
					classname="CountryEvent",
					country = sender.country,
					message = 0)

government_overthrown.connect(log_overthrow)

def log_conquering(sender, **kwargs):
	assert isinstance(sender, Player), "sender must be a Player"
	log_event(CountryEvent, sender.game,
					classname="CountryEvent",
					country = kwargs['country'],
					message = 1)

country_conquered.connect(log_conquering)

def log_excommunication(sender, **kwargs):
	assert isinstance(sender, Player), "sender must be a Player"
	log_event(CountryEvent, sender.game,
					classname="CountryEvent",
					country = sender.country,
					message = 2)

country_excommunicated.connect(log_excommunication)

def log_elimination(sender, **kwargs):
	assert isinstance(sender, Player), "sender must be a Player"
	log_event(CountryEvent, sender.game,
					classname="CountryEvent",
					country = kwargs['country'],
					message = 3)

country_eliminated.connect(log_elimination)

DISASTER_EVENTS = (
	(0, _('is affected by famine.')),
	(1, _('has been affected by plague.'))
)

class DisasterEvent(BaseEvent):
	""" Event triggered when a province is affected by a natural disaster.

	Currently, the conditions are:
	
	* The province is affected by famine.
	
	* The province is affected by plague.
	
	Each condition must have its own signal.
	"""
	area = models.ForeignKey(Area)
	message = models.PositiveIntegerField(choices=DISASTER_EVENTS)

	def __unicode__(self):
		return "%(area)s %(message)s" % {
									'area': self.area.name,
									'message': self.get_message_display()
									}
	
	def event_class(self):
		return "season_%(season)s" % {'season': self.season}

def log_famine_marker(sender, **kwargs):
	assert isinstance(sender, GameArea), "sender must be a GameArea"
	log_event(DisasterEvent, sender.game,
					classname="DisasterEvent",
					area = sender.board_area,
					message = 0)

famine_marker_placed.connect(log_famine_marker)

def log_plague(sender, **kwargs):
	assert isinstance(sender, GameArea), "sender must be a GameArea"
	log_event(DisasterEvent, sender.game,
					classname="DisasterEvent",
					area = sender.board_area,
					message = 1)

plague_placed.connect(log_plague)

class IncomeEvent(BaseEvent):
	""" Event triggered when a country receives income """
	country = models.ForeignKey(Country)
	ducats = models.PositiveIntegerField()

	def event_class(self):
		return "income-event"

	def __unicode__(self):
		return _("%(country)s raises %(ducats)s ducats.") % {
						'country': self.country,
						'ducats': self.ducats,
						}

def log_income(sender, **kwargs):
	assert isinstance(sender, Player), "sender must be a Player"
	log_event(IncomeEvent, sender.game,
					classname="IncomeEvent",
					country=sender.country,
					ducats=kwargs['ducats'])

income_raised.connect(log_income)
