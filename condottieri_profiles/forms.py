from django.forms import ModelForm

from condottieri_profiles.models import *

class ProfileForm(ModelForm):
	class Meta:
		model = CondottieriProfile
		exclude = ('user',)
