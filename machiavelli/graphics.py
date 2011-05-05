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

""" This module defines functions to generate the map. """

import Image
import os

from django.conf import settings

BASEDIR=os.path.join(settings.PROJECT_ROOT, 'machiavelli/media/machiavelli/tokens')
BASEMAP='base-map.png'
if settings.DEBUG:
	MAPSDIR = os.path.join(settings.PROJECT_ROOT, 'machiavelli/media/machiavelli/maps')
else:
	MAPSDIR = os.path.join(settings.MEDIA_ROOT, 'maps')

def make_map(game):
	""" Opens the base map and add flags, control markers, unit tokens and other tokens. Then saves
	the map with an appropriate name in the maps directory.
	"""
	base_map = Image.open(os.path.join(BASEDIR, BASEMAP))
	garrisons = []
	for player in game.player_set.filter(user__isnull=False):
		## paste control markers
		controls = player.gamearea_set.all()
		marker = Image.open("%s/control-%s.png" % (BASEDIR, player.country.css_class))
		for area in controls:
			base_map.paste(marker, (area.board_area.controltoken.x, area.board_area.controltoken.y), marker)
		## paste flags
		home = player.home_country()
		flag = Image.open("%s/flag-%s.png" % (BASEDIR, player.country.css_class))
		for game_area in home:
			area = game_area.board_area
			base_map.paste(flag, (area.controltoken.x, area.controltoken.y - 15), flag)
		## paste As and Fs (not garrisons because of sieges)
		units = player.unit_set.all()
		army = Image.open("%s/A-%s.png" % (BASEDIR, player.country.css_class))
		fleet = Image.open("%s/F-%s.png" % (BASEDIR, player.country.css_class))
		for unit in units:
			if unit.besieging:
				coords = (unit.area.board_area.gtoken.x, unit.area.board_area.gtoken.y)
			else:
				coords = (unit.area.board_area.aftoken.x, unit.area.board_area.aftoken.y)
			if unit.type == 'A':
				base_map.paste(army, coords, army)
			elif unit.type == 'F':
				base_map.paste(fleet, coords, fleet)
			else:
				pass
	## paste garrisons
	for player in game.player_set.all():
		if player.user:
			garrison = Image.open("%s/G-%s.png" % (BASEDIR, player.country.css_class))
		else:
			## autonomous
			garrison = Image.open("%s/G-autonomous.png" % BASEDIR)
		for unit in player.unit_set.filter(type__exact='G'):
			coords = (unit.area.board_area.gtoken.x, unit.area.board_area.gtoken.y)
			base_map.paste(garrison, coords, garrison)
	## paste famine markers
	if game.configuration.famine:
		famine = Image.open("%s/famine-marker.png" % BASEDIR)
		for a in game.gamearea_set.filter(famine=True):
			coords = (a.board_area.aftoken.x + 16, a.board_area.aftoken.y + 16)
			base_map.paste(famine, coords, famine)
	## paste rebellion markers
	if game.configuration.finances:
		rebellion_marker = Image.open("%s/rebellion-marker.png" % BASEDIR)
		for r in game.get_rebellions():
			if r.garrisoned:
				coords = (r.area.board_area.gtoken.x, r.area.board_area.gtoken.y)
			else:
				coords = (r.area.board_area.aftoken.x, r.area.board_area.aftoken.y)
			base_map.paste(rebellion_marker, coords, rebellion_marker)
	## save the map
	result = base_map #.resize((1250, 1780), Image.ANTIALIAS)
	filename = os.path.join(MAPSDIR, "map-%s.jpg" % game.pk)
	result.save(filename)
	return True

def make_scenario_map(s):
	""" Makes the initial map for an scenario.
	"""
	base_map = Image.open(os.path.join(BASEDIR, BASEMAP))
	for c in s.get_countries():
		## paste control markers and flags
		controls = s.home_set.filter(country=c, is_home=True)
		marker = Image.open("%s/control-%s.png" % (BASEDIR, c.static_name))
		flag = Image.open("%s/flag-%s.png" % (BASEDIR, c.static_name))
		for h in controls:
			base_map.paste(marker, (h.area.controltoken.x, h.area.controltoken.y), marker)
			base_map.paste(flag, (h.area.controltoken.x, h.area.controltoken.y - 15), flag)
		## paste units
		army = Image.open("%s/A-%s.png" % (BASEDIR, c.static_name))
		fleet = Image.open("%s/F-%s.png" % (BASEDIR, c.static_name))
		garrison = Image.open("%s/G-%s.png" % (BASEDIR, c.static_name))
		for setup in c.setup_set.filter(scenario=s):
			if setup.unit_type == 'G':
				coords = (setup.area.gtoken.x, setup.area.gtoken.y)
				base_map.paste(garrison, coords, garrison)
			elif setup.unit_type == 'A':
				coords = (setup.area.aftoken.x, setup.area.aftoken.y)
				base_map.paste(army, coords, army)
			elif setup.unit_type == 'F':
				coords = (setup.area.aftoken.x, setup.area.aftoken.y)
				base_map.paste(fleet, coords, fleet)
			else:
				pass
	## paste autonomous garrisons
	garrison = Image.open("%s/G-autonomous.png" % BASEDIR)
	for g in s.setup_set.filter(country__isnull=True, unit_type='G'):
		coords = (g.area.gtoken.x, g.area.gtoken.y)
		base_map.paste(garrison, coords, garrison)
	## save the map
	result = base_map #.resize((1250, 1780), Image.ANTIALIAS)
	filename = os.path.join(MAPSDIR, "scenario-%s.jpg" % s.pk)
	result.save(filename)
	return True
