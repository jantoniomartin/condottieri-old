import os

from django.conf import settings

SNAPSHOTS_DIR = os.path.join(settings.PROJECT_ROOT, 'machiavelli/media/machiavelli/maps/snapshots')

def save_snapshot(game):
	filename = "%s.snap" % game.id
	try:
		path = os.path.join(SNAPSHOTS_DIR, filename)
		fd = open(path, mode='a')
	except IOError, v:
		print v
		return
	else:
		fd.write("\n")
		fd.write("<turn year=\"%s\" season=\"%s\">\n" % (game.year, game.season))
		for player in game.player_set.all():
			if player.country:
				fd.write("<player country=\"%s\">\n" % (player.country))
			else:
				fd.write("<player>\n")
			for unit in player.unit_set.all():
				fd.write("<unit ")
				fd.write("id=\"%(id)s\" type=\"%(type)s\" area=\"%(area)s\" besieging=\"%(bes)s\" />" %
							{ 'id': unit.id,
							  'type': unit.type,
							  'area': unit.area.board_area.code,
							  'bes': unit.besieging })
				fd.write("\n")
			fd.write("</player>\n")
		fd.write("</turn>\n")
		fd.close()
