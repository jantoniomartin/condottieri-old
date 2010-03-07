from machiavelli.models import *
from django.contrib import admin

class ScenarioAdmin(admin.ModelAdmin):
	list_display = ('title', 'start_year')

class CountryAdmin(admin.ModelAdmin):
	list_display = ('name', 'css_class')

class PlayerAdmin(admin.ModelAdmin):
	list_display = ('user', 'game', 'country', 'done')

class UnitAdmin(admin.ModelAdmin):
	list_display = ('player', 'area', 'type')

class GameAreaAdmin(admin.ModelAdmin):
	list_display = ('game', 'board_area', 'player')

class SetupAdmin(admin.ModelAdmin):
	list_display = ('scenario', 'country', 'area', 'unit_type')

class OrderAdmin(admin.ModelAdmin):
	pass

class ControlTokenInline(admin.TabularInline):
	model = ControlToken
	extra = 1

class GTokenInline(admin.TabularInline):
	model = GToken
	extra = 1

class AFTokenInline(admin.TabularInline):
	model = AFToken
	extra = 1

class AreaAdmin(admin.ModelAdmin):
	list_display = ('name', 'code', 'is_sea', 'is_coast', 'has_city', 'is_fortified', 'has_port')
	inlines = [ ControlTokenInline,
		GTokenInline,
		AFTokenInline ]

class LogAdmin(admin.ModelAdmin):
	list_display = ('game', 'year', 'season', 'event')

class LogInline(admin.TabularInline):
	model = Log
	max_num = 10

class GameAdmin(admin.ModelAdmin):
	list_display = ('pk', 'year', 'season', 'phase', 'slots', 'scenario', 'created_by')
	inlines = [LogInline,]

class RetreatOrderAdmin(admin.ModelAdmin):
	pass

class LetterAdmin(admin.ModelAdmin):
	pass

admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(GameArea, GameAreaAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Setup, SetupAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(RetreatOrder, RetreatOrderAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Letter, LetterAdmin)
