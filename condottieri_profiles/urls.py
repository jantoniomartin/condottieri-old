from django.conf.urls.defaults import *
#from django.views.generic import list_detail
#from django.views.generic.create_update import create_object
from django.views.generic.simple import direct_to_template
from django.views.decorators.cache import cache_page


urlpatterns = patterns('condottieri_profiles.views',
    #url(r'^$', 'game_list', name='game-list'),
	url(r'^profile/(?P<username>\w+)', 'profile_detail', name='profile_detail'),
	url(r'^edit$', 'profile_edit', name='profile_edit'),
)
