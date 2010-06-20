from django.core.management.base import NoArgsCommand, CommandError

from machiavelli import models

class Command(NoArgsCommand):

	def handle_noargs(self, **options):
		setups = models.Setup.objects.all().order_by('scenario', 'area')
		for s in setups:
			## if there is a non-autonomous unit, create a Home object
			if s.country and s.unit_type:
				print "Creating home for %s in %s" % (s.country, s.area)
				home = models.Home(scenario = s.scenario,
								country = s.country,
								area = s.area)
				home.save()
			## if there is no unit, delete the setup object
			if not s.unit_type:
				print "Deleting setup in %s" % s.area
				s.delete()
