from django.conf import settings
from django.utils.translation import ugettext_noop as _
from django.db.models import signals

if "notification" in settings.INSTALLED_APPS:
	from notification import models as notification

	def create_notice_types(app, created_models, verbosity, **kwargs):
		print "Creating notices for condottieri_profiles"
		notification.create_notice_type("karma_healed",
										_("Karma healed"),
										_("you have recovered the minimum karma to join games"))

	signals.post_syncdb.connect(create_notice_types, sender=notification)
else:
	print "Skipping creation of NoticeTypes as notification app not found"
