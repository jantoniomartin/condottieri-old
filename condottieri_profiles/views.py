## django
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

## condottieri_profiles
from condottieri_profiles.models import *
from condottieri_profiles.forms import *

@login_required
def profile_detail(request, username=''):
	profile = get_object_or_404(CondottieriProfile, user__username=username)
	is_own = (request.user == profile.user)

	return render_to_response('condottieri_profiles/profile_detail.html',
							{'profile': profile,
							'is_own': is_own},
							context_instance=RequestContext(request))

@login_required
def profile_edit(request):
	if request.method == 'POST':
		form = ProfileForm(data=request.POST,
							instance=request.user.get_profile())
		if form.is_valid():
			form.save()
			return redirect(request.user.get_profile())
	else:	
		form = ProfileForm(instance=request.user.get_profile())

	return render_to_response('condottieri_profiles/profile_form.html',
							{'form': form,},
							context_instance=RequestContext(request))
