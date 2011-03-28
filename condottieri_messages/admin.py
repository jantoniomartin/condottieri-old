from condottieri_messages.models import *
from django.contrib import admin

class LetterAdmin(admin.ModelAdmin):
	list_per_page = 20
	list_display = ('subject', 'sender_player', 'recipient_player', 'year', 'season')

admin.site.register(Letter, LetterAdmin)
