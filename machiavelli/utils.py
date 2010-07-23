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

from machiavelli.models import Unit

def order_is_possible(order):
	""" Returns the order if it is possible, as stated in the rules, or False if not"""
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
			if order.subunit.type == 'A':
				if order.unit.area.board_area.is_sea:
					return order
	elif order.code == 'S':
		if order.unit.type == 'G':
			if order.subcode == '-' and order.subdestination == order.unit.area:
				return order
			if order.subcode == 'H' and order.subunit.area == order.unit.area:
				return order
		elif order.unit.type == 'F':
			if order.subcode == '-':
				sup_area = order.subdestination.board_area
			elif order.subcode in ('H', 'B', '='):
				sup_area = order.subunit.area.board_area
			if sup_area.is_sea or sup_area.is_coast:
				if sup_area.is_adjacent(order.unit.area.board_area, fleet=True):
					return order
		elif order.unit.type == 'A':
			if order.subcode == '-':
				sup_area = order.subdestination.board_area
			elif order.subcode in ('H', 'B', '='):
				sup_area = order.subunit.area.board_area
			if not sup_area.is_sea and sup_area.is_adjacent(order.unit.area.board_area):
				return order
	return False
