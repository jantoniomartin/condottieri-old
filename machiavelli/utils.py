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

""" This module defines miscellaneous functions. """

import random

from django.db.models import Q
from django.conf import settings

if "jogging" in settings.INSTALLED_APPS:
	from jogging import logging
else:
	logging = None

from machiavelli.models import Unit

def order_is_possible(order):
	""" Checks if an Order is possible as stated in the rules.

	If ``order`` is possible, returns the same ``order``. If not, returns False.
	"""

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
		## only fortified cities can be besieged
		if order.unit.area.board_area.is_fortified:
			## only As and Fs in ports can besiege
			if order.unit.type == 'A' or (order.unit.type == 'F' and order.unit.area.board_area.has_port):
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
