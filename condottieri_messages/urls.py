from django.conf.urls.defaults import *
#from django.views.generic import list_detail
#from django.views.generic.create_update import create_object
from django.views.generic.simple import redirect_to #direct_to_template
#from django.views.decorators.cache import cache_page

from messages.views import *

## urls that call the views in messages
urlpatterns = patterns('messages.views',
    url(r'^$', redirect_to, {'url': 'inbox/'}),
	url(r'^inbox/$', inbox, {'template_name': 'condottieri_messages/inbox.html',}, name='messages_inbox'),
    url(r'^outbox/$', outbox, {'template_name': 'condottieri_messages/outbox.html',}, name='messages_outbox'),
    url(r'^delete/(?P<message_id>[\d]+)/$', 'delete', name='messages_delete'),
    url(r'^undelete/(?P<message_id>[\d]+)/$', 'undelete', name='messages_undelete'),
    url(r'^trash/$', trash, {'template_name': 'condottieri_messages/trash.html',}, name='messages_trash'),
)

## urls that call the custom views in condottieri_messages
urlpatterns += patterns('condottieri_messages.views',
	url(r'^compose/(?P<sender_id>[\d]+)/(?P<recipient_id>[\d]+)/$', 'compose', name='condottieri_messages_compose'),
    url(r'^reply/(?P<letter_id>[\d]+)/$', 'reply', name='condottieri_messages_reply'),
    url(r'^view/(?P<message_id>[\d]+)/$', 'view', name='condottieri_messages_detail'),
)
