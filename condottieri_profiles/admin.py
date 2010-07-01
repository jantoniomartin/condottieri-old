from condottieri_profiles.models import *
from django.contrib import admin

class CondottieriProfileAdmin(admin.ModelAdmin):
	ordering = ['user__username']
	list_display = ('__unicode__', 'location', 'karma', 'total_score')

admin.site.register(CondottieriProfile, CondottieriProfileAdmin)
