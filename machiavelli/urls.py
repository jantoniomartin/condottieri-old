from django.conf.urls.defaults import *
#from django.views.generic import list_detail
#from django.views.generic.create_update import create_object
from django.views.generic.simple import direct_to_template
from django.views.decorators.cache import cache_page


#urlpatterns = patterns('inon.machiavelli.views',
urlpatterns = patterns('machiavelli.views',
    #url(r'^$', 'game_list', name='game-list'),
	url(r'^$', 'summary', name='summary'),
	url(r'^games$', 'game_list', name='game-list'),
	url(r'^scenario/(?P<scenario_id>\d+)', 'show_scenario', name='show-scenario'),
	url(r'^faq$', cache_page(direct_to_template, 24*60*60), {'template': 'machiavelli/faq.html'}, name='faq'),
	url(r'^ranking$', 'hall_of_fame', name='hall-of-fame'),
	url(r'^overthrow/(?P<revolution_id>\d+)', 'overthrow', name='overthrow'),
	url(r'^new_game$', 'create_game', name='new-game'),
	url(r'^game/(?P<slug>[-\w]+)/join$', 'join_game', name='join-game'),
	url(r'^game/(?P<slug>[-\w]+)/leave$', 'leave_game', name='leave-game'),
	url(r'^game/(?P<slug>[-\w]+)/log$', 'logs_by_game', name='game-log'),
	url(r'^game/(?P<slug>[-\w]+)/turn$', 'turn_log_list', name='turn-log-list'),
	url(r'^game/(?P<slug>[-\w]+)/inbox$', 'box_list', {'box': 'inbox'}, name='inbox'),
	url(r'^game/(?P<slug>[-\w]+)/outbox$', 'box_list', {'box': 'outbox'}, name='outbox'),
	url(r'^game/(?P<slug>[-\w]+)/results$', 'game_results', name='game-results'),
	url(r'^game/(?P<slug>[-\w]+)/excommunicate/(?P<player_id>\d+)', 'excommunicate', name='excommunicate'),
	url(r'^game/(?P<slug>[-\w]+)/reset_excom$', 'reset_excommunications', name='reset-excommunications'),
	url(r'^game/(?P<slug>[-\w]+)/confirm_orders$', 'confirm_orders', name='confirm-orders'),
	url(r'^game/(?P<slug>[-\w]+)/delete_order/(?P<order_id>\d+)$', 'delete_order', name='delete-order'),
	url(r'^game/(?P<slug>[-\w]+)', 'play_game', name='show-game'),
	#url(r'^jsgame/(?P<slug>[-\w]+)', 'js_play_game', name='js-play-game'),
	url(r'^letter/new/(?P<sender_id>\d+)/(?P<receiver_id>\d+)', 'new_letter', name='new-letter'),
	url(r'^letter/(?P<letter_id>\d+)', 'show_letter', name='show-letter'),
)

