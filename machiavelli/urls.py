from django.conf.urls.defaults import *
#from django.views.generic import list_detail
#from django.views.generic.create_update import create_object
from django.views.generic.simple import direct_to_template
from django.views.decorators.cache import cache_page


#urlpatterns = patterns('inon.machiavelli.views',
urlpatterns = patterns('machiavelli.views',
    url(r'^$', 'game_list', name='game-list'),
	url(r'^scenario/(?P<scenario_id>\d+)', 'show_scenario', name='show-scenario'),
	url(r'^faq$', cache_page(direct_to_template, 24*60*60), {'template': 'machiavelli/faq.html'}, name='faq'),
	url(r'^ranking$', 'hall_of_fame', name='hall-of-fame'),
	url(r'^game/new$', 'create_game', name='new-game'),
	url(r'^game/join/(?P<game_id>\d+)', 'join_game', name='join-game'),
	url(r'^game/overthrow/(?P<revolution_id>\d+)', 'overthrow', name='overthrow'),
	url(r'^game/log/(\d+)', 'logs_by_game', name='game-log'),
	url(r'^game/inbox/(\d+)', 'box_list', {'box': 'inbox'}, name='inbox'),
	url(r'^game/outbox/(\d+)', 'box_list', {'box': 'outbox'}, name='outbox'),
	url(r'^letter/new/(?P<sender_id>\d+)/(?P<receiver_id>\d+)', 'new_letter', name='new-letter'),
	url(r'^letter/(?P<letter_id>\d+)', 'show_letter', name='show-letter'),
	url(r'^game/(?P<game_id>\d+)', 'play_game', name='show-game'),
	url(r'^game/results/(?P<game_id>\d+)', 'game_results', name='game-results'),
	#url(r'^game/(?P<slug>[-\w]+)$', 'play_game', name='show-game'),
)

