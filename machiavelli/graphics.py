##
## Library of graphic functions
## 

import Image
import os
from datetime import datetime

from django.conf import settings


BASEDIR=os.path.join(settings.PROJECT_ROOT, 'machiavelli/media/machiavelli/tokens')
BASEMAP='base-map.png'
if settings.DEBUG:
	MAPSDIR = os.path.join(settings.PROJECT_ROOT, 'machiavelli/media/machiavelli/maps')
else:
	MAPSDIR = os.path.join(settings.STATIC_ROOT, 'machiavelli/maps')

def make_map(game):
	"""
	Open the base map, and add flags, control markers and unit tokens
	"""
	start_dt = datetime.now()
	print "Starting map generation for game %s at %s" % (game, start_dt)
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
	## save the map
	result = base_map #.resize((1250, 1780), Image.ANTIALIAS)
	filename = os.path.join(MAPSDIR, "map-%s.jpg" % game.pk)
	result.save(filename)
	game.map_saved()
	td_lapse = datetime.now() - start_dt
	print "Processed map in %s seconds." % td_lapse.seconds
	return True
