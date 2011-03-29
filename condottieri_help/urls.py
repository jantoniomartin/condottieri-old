from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.decorators.cache import cache_page

from django.conf import settings

extra_context = {
	'contact_email': settings.CONTACT_EMAIL,
	'forum_url': '/forum',
}

urlpatterns = patterns('condottieri_help.views',
    url(r'^$', direct_to_template, {'template': 'condottieri_help/index.html', 'extra_context': extra_context}, name='help-index'),
)

