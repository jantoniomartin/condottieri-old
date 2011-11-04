from condottieri_profiles.models import *
from django.contrib import admin

class SpokenLanguageInline(admin.TabularInline):
	model = SpokenLanguage
	extra = 1

class CondottieriProfileAdmin(admin.ModelAdmin):
	ordering = ['user__username']
	list_display = ('__unicode__', 'location', 'website', 'karma', 'total_score', 'weighted_score', 'overthrows')
	inlines = [SpokenLanguageInline, ]

admin.site.register(CondottieriProfile, CondottieriProfileAdmin)
