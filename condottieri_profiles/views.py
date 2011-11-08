## django
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

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
	profile = request.user.get_profile()
	if request.method == 'POST':
		form = ProfileForm(data=request.POST, instance=profile)
		if form.is_valid():
			form.save()
			messages.success(request, _("Your profile has been updated."))
			return redirect(profile)
	else:	
		form = ProfileForm(instance=profile)

	return render_to_response('condottieri_profiles/profile_form.html',
							{'form': form,},
							context_instance=RequestContext(request))

@login_required
def languages_edit(request):
	profile = request.user.get_profile()
	LangInlineFormSet = inlineformset_factory(CondottieriProfile, SpokenLanguage, extra=1)
	if request.method == 'POST':
		formset = LangInlineFormSet(request.POST, instance=profile)
		if formset.is_valid():
			formset.save()
			messages.success(request, _("Your languages have been updated."))
			return redirect(profile)
	else:
		formset = LangInlineFormSet(instance=profile)

	return render_to_response('condottieri_profiles/language_form.html',
							{'formset': formset,},
							context_instance=RequestContext(request))
