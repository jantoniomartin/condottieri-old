from django.conf.urls.defaults import *
from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_page
from django.views.generic.simple import direct_to_template

from django.contrib import admin
admin.autodiscover()

#from account.openid_consumer import PinaxConsumer
from waitinglist.forms import WaitingListEntryForm

handler500 = "pinax.views.server_error"


# @@@ turn into template tag
#def homepage(request):
#    if request.method == "POST":
#        form = WaitingListEntryForm(request.POST)
#        if form.is_valid():
#            form.save()
#            return HttpResponseRedirect(reverse("waitinglist_sucess"))
#    else:
#        form = WaitingListEntryForm()
#    return direct_to_template(request, "homepage.html", {
#        "form": form,
#    })


if settings.ACCOUNT_OPEN_SIGNUP:
    signup_view = "account.views.signup"
else:
    signup_view = "signup_codes.views.signup"


urlpatterns = patterns('',
	url(r'^$', 'machiavelli.views.summary', name='home'),
    url(r'^success/$', direct_to_template, {"template": "waitinglist/success.html"}, name="waitinglist_sucess"),
    
    url(r'^admin/invite_user/$', 'signup_codes.views.admin_invite_user', name="admin_invite_user"),
    url(r'^account/signup/$', signup_view, name="acct_signup"),
    
    (r'^about/', include('about.urls')),
    (r'^account/', include('account.urls')),
    #(r'^openid/(.*)', PinaxConsumer()),
    #(r'^profiles/', include('basic_profiles.urls')),
    (r'^notices/', include('notification.urls')),
    #(r'^announcements/', include('announcements.urls')),
    
    (r'^admin/(.*)', admin.site.root),
		
	## machiavelli urls
	(r'^machiavelli/', include('machiavelli.urls')),
	(r'^profiles/', include('condottieri_profiles.urls')),
	
	## forum urls
	(r'^forum/', include('forum.urls')),

	## avatar urls
	(r'^avatar/', include('avatar.urls')),
	## django-messages
	(r'^mail/', include('condottieri_messages.urls')),
)

if settings.SERVE_MEDIA:
	from staticfiles.urls import staticfiles_urlpatterns
	urlpatterns += staticfiles_urlpatterns()
    #urlpatterns += patterns('',
    #    (r'^site_media/', include('staticfiles.urls')),
    #)
