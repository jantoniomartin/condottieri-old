from condottieri_profiles.models import *
from django.contrib import admin

class CondottieriProfileAdmin(admin.ModelAdmin):
	ordering = ['user__username']
	list_display = ('__unicode__', 'location', 'website', 'karma', 'total_score', 'weighted_score', 'overthrows')

admin.site.register(CondottieriProfile, CondottieriProfileAdmin)
