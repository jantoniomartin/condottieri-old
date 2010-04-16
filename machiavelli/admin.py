from machiavelli.models import *
from django.contrib import admin

class ScenarioAdmin(admin.ModelAdmin):
	list_display = ('title', 'start_year')

class CountryAdmin(admin.ModelAdmin):
	list_display = ('name', 'css_class')

class PlayerAdmin(admin.ModelAdmin):
	list_display = ('user', 'game', 'country', 'done')

class UnitAdmin(admin.ModelAdmin):
	list_display = ('__unicode__', 'player')
	ordering = ['player']

class GameAreaAdmin(admin.ModelAdmin):
	list_display = ('game', 'board_area', 'player')
	list_per_page = 73
	ordering = ['board_area']

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

#class LogAdmin(admin.ModelAdmin):
#	list_display = ('game', 'year', 'season', 'event')

#class LogInline(admin.TabularInline):
#	model = Log
#	max_num = 10

class BaseEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20
	list_display = ('__unicode__', 'year', 'season', 'phase')

class NewUnitEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20

class DisbandEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20

class OrderEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20

class StandoffEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20

class ConversionEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20

class ControlEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20

class MovementEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20

class UnitEventAdmin(admin.ModelAdmin):
	#ordering = ['-id']
	list_per_page = 20

class GameAdmin(admin.ModelAdmin):
	list_display = ('pk', 'year', 'season', 'phase', 'slots', 'scenario', 'created_by')
	#inlines = [LogInline,]

class RetreatOrderAdmin(admin.ModelAdmin):
	pass

class LetterAdmin(admin.ModelAdmin):
	ordering = ['-id']
	list_display = ('sender', 'receiver', '__unicode__')

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
#admin.site.register(Log, LogAdmin)
admin.site.register(BaseEvent, BaseEventAdmin)
admin.site.register(NewUnitEvent, NewUnitEventAdmin)
admin.site.register(DisbandEvent, DisbandEventAdmin)
admin.site.register(OrderEvent, OrderEventAdmin)
admin.site.register(StandoffEvent, StandoffEventAdmin)
admin.site.register(ConversionEvent, ConversionEventAdmin)
admin.site.register(ControlEvent, ControlEventAdmin)
admin.site.register(MovementEvent, MovementEventAdmin)
admin.site.register(UnitEvent, UnitEventAdmin)
admin.site.register(Letter, LetterAdmin)
