##
## Functions library
##
import random

#import django.forms as forms
#from django.forms.formsets import BaseFormSet
from django.db.models import Q
from django.conf import settings

if "jogging" in settings.INSTALLED_APPS:
	from jogging import logging
else:
	logging = None

from machiavelli.models import Area, Unit, Order

def parse_order_form(data):
	if logging:
		logging.debug("Parsing order form: %s" % data)
	order = Order(unit=data['unit'], code = data['code'])
	if order.code == '-':
		order.destination = data['destination']
		if order.destination == None:
			return False
	elif order.code == '=':
		order.type = data['conversion']
		if order.type == None:
			return False
	elif order.code == 'C' or order.code == 'S':
		if data['subunit'] == None:
			return False
		subunit_abbr = "%s %s" % (data['subunit'].type, data['subunit'].area.board_area.code)
		if order.code == 'S':
			suborder = "%s %s" % (subunit_abbr, data['subcode'])
			if data['subcode'] == '-':
				if data['subdestination'] == None:
					return False
				suborder += " %s" % data['subdestination'].board_area.code
			elif data['subcode'] == '=':
				suborder += " = %s" % data['subconversion']
		elif order.code == 'C':
			if data['subdestination'] == None:
				return False
			else:
				suborder = "%s - %s" % (subunit_abbr, data['subdestination'].board_area.code)
		order.suborder = suborder
	return order_is_possible(order)

def parse_support_order(data):
	if logging:
		logging.debug("Parsing support order %s" % data)
	area_codes = Area.objects.values_list('code')
	params = data.upper().strip().split(' ')
	if len(params) < 3 or len(params) > 4:
		raise ValueError, "Wrong order format"
	order = {}
	order['type'] = params[0]
	if not order['type'] in ('A', 'F', 'G'):
		raise ValueError, "Wrong unit type %s" % order['type']
	order['origin'] = params[1]
	if not (order['origin'], ) in area_codes:
		raise ValueError, "Wrong area %s" % order['origin']
	order['code'] = params[2]
	if not order['code'] in ('H', 'B', '-', '='):
		raise ValueError, "Wrong order code %s" % order['code']
	if len(params) == 4:
		if params[2] == '-':
			if (params[3], ) in area_codes:
				order['destination'] = params[3]
			else:
				raise ValueError, "Wrong destination %s" % params[3]
		elif params[2] == '=':
			if params[3] in ('A', 'F', 'G'):
				order['conversion'] = params[3]
			else:
				raise ValueError, "Wrong unit type %s" % params[3]
	return order

def order_is_possible(order):
	""" Returns the order if the it is possible, as stated in the rules, or False if not"""
	if logging:
		logging.debug("Checking if order is possible: %s" % order)
	if order.code == 'H':
		return order
	elif order.code == '-':
		## only A and F can advance
		if order.unit.type == 'A':
			## it only can advance to adjacent or coastal provinces (with convoy)
			## it cannot go to Venice
			if order.unit.area.board_area.is_coast and order.destination.board_area.is_coast and order.destination.board_area.code != 'VEN':
				return order
			if order.unit.area.board_area.is_adjacent(order.destination.board_area):
				return order
		elif order.unit.type == 'F':
			## it only can go to adjacent seas or coastal provinces
			if order.destination.board_area.is_sea or order.destination.board_area.is_coast:
				if order.unit.area.board_area.is_adjacent(order.destination.board_area, fleet=True):
					return order
	elif order.code == 'B':
		## only A and F can besiege
		if order.unit.type in ('A', 'F') and order.unit.area.board_area.is_fortified:
			## is there an enemy Garrison in the city
			try:
				gar = Unit.objects.get(type='G', area=order.unit.area)
			except:
				return False
			else:
				if gar.player != order.unit.player:
					return order
	elif order.code == '=':
		if order.unit.area.board_area.is_fortified:
			if order.unit.type == 'G':
				if order.type == 'A':
					return order
				if order.type == 'F' and order.unit.area.board_area.has_port:
					return order
			if order.type == 'G':
				try:
					## if there is already a garrison, the unit cannot be converted
					gar = Unit.objects.get(type='G', area=order.unit.area)
				except:
					if order.unit.type == 'A':
						return order
					if order.unit.type == 'F' and order.unit.area.board_area.has_port:
						return order
	elif order.code == 'C':
		if order.unit.type == 'F':
			if order.suborder[0] == 'A':
				if order.unit.area.board_area.is_sea:
					return order
	elif order.code == 'S':
		parsed = parse_support_order(order.suborder)
		if order.unit.type == 'G':
			if parsed['code'] == '-' and parsed['destination'] == order.unit.area.board_area.code:
				return order
			if parsed['code'] == 'H' and parsed['origin'] == order.unit.area.board_area.code:
				return order
		elif order.unit.type == 'F':
			if parsed['code'] == '-':
				sup_area = Area.objects.get(code__exact=parsed['destination'])
			elif parsed['code'] in ('H', 'B', '='):
				sup_area = Area.objects.get(code__exact=parsed['origin'])
			if sup_area.is_sea or sup_area.is_coast:
				if sup_area.is_adjacent(order.unit.area.board_area, fleet=True):
					return order
		elif order.unit.type == 'A':
			if parsed['code'] == '-':
				sup_area = Area.objects.get(code__exact=parsed['destination'])
			elif parsed['code'] in ('H', 'B', '='):
				sup_area = Area.objects.get(code__exact=parsed['origin'])
			if not sup_area.is_sea and sup_area.is_adjacent(order.unit.area.board_area):
				return order
	return False

