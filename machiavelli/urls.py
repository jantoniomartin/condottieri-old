from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.views.generic.create_update import create_object


#urlpatterns = patterns('inon.machiavelli.views',
urlpatterns = patterns('machiavelli.views',
    url(r'^$', 'game_list', name='game-list'),
	#url(r'^scenario/(?P<object_id>\d+)', list_detail.object_detail, scenario_context, name='scenario-detail'),
	url(r'^ranking$', 'hall_of_fame', name='hall-of-fame'),
	url(r'^game/new$', 'create_game', name='new-game'),
	url(r'^game/join/(?P<game_id>\d+)', 'join_game', name='join-game'),
	url(r'^game/log/(\d+)', 'logs_by_game', name='game-log'),
	url(r'^game/inbox/(\d+)', 'box_list', {'box': 'inbox'}, name='inbox'),
	url(r'^game/outbox/(\d+)', 'box_list', {'box': 'outbox'}, name='outbox'),
	url(r'^letter/new/(?P<sender_id>\d+)/(?P<receiver_id>\d+)', 'new_letter', name='new-letter'),
	url(r'^letter/(?P<letter_id>\d+)', 'show_letter', name='show-letter'),
	url(r'^game/(?P<game_id>\d+)', 'play_game', name='show-game'),
	url(r'^game/results/(?P<game_id>\d+)', 'game_results', name='game-results'),
	#url(r'^game/(?P<slug>[-\w]+)$', 'play_game', name='show-game'),
)

