from machiavelli.models import *
from django.contrib import admin

class SetupInline(admin.TabularInline):
	model = Setup
	extra = 5
	ordering = ['country']

class HomeInline(admin.TabularInline):
	model = Home
	extra = 5
	ordering = ['country']

class ScenarioAdmin(admin.ModelAdmin):
	list_display = ('title', 'start_year')
	inlines = [HomeInline, SetupInline,]

class CountryAdmin(admin.ModelAdmin):
	list_display = ('name', 'css_class')

class PlayerAdmin(admin.ModelAdmin):
	list_display = ('user', 'game', 'country', 'done')
	list_filter = ('game', 'done')
	ordering = ['game']

class RevolutionAdmin(admin.ModelAdmin):
	list_display = ('government', 'opposition')

class ScoreAdmin(admin.ModelAdmin):
	list_display = ('user', 'game', 'country', 'points', 'cities')
	list_filter = ('game', 'user', 'country')
	ordering = ['game']

class UnitAdmin(admin.ModelAdmin):
	list_display = ('__unicode__', 'player', 'must_retreat')
	ordering = ['player']
	list_filter = ('player', 'must_retreat')

class GameAreaAdmin(admin.ModelAdmin):
	list_display = ('game', 'board_area', 'player', 'standoff', 'famine')
	list_per_page = 73
	ordering = ['board_area']
	list_filter = ('game', 'player', 'standoff', 'famine')

class SetupAdmin(admin.ModelAdmin):
	list_display = ('scenario', 'country', 'area', 'unit_type')

class OrderAdmin(admin.ModelAdmin):
	list_display = ('player_info', '__unicode__', 'explain', 'confirmed')
	list_filter = ('confirmed',)

	def player_info(self, obj):
		return "%(country)s (%(game)s)" % { 'country': obj.unit.player.country,
											'game': obj.unit.player.game }
	player_info.short_description = 'Player'

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

class ConfigurationInline(admin.TabularInline):
	model = Configuration
	extra = 1

class GameAdmin(admin.ModelAdmin):
	list_display = ('pk', 'slug', 'year', 'season', 'phase', 'slots', 'scenario', 'created_by', 'next_phase_change', 'player_list')
	actions = ['redraw_map']
	inlines = [ ConfigurationInline, ]

	def redraw_map(self, request, queryset):
		for obj in queryset:
			obj.make_map()
	redraw_map.short_description = "Redraw map"
	
	def player_list(self, obj):
		users = []
		for p in obj.player_set.filter(user__isnull=False):
			users.append(p.user.username)
		return ", ".join(users)

	player_list.short_description = 'Player list'

class RetreatOrderAdmin(admin.ModelAdmin):
	pass

class LetterAdmin(admin.ModelAdmin):
	ordering = ['-id']
	list_display = ('sender', 'receiver', '__unicode__')

class TurnLogAdmin(admin.ModelAdmin):
	ordering = ['-timestamp']
	list_display = ('game', 'timestamp')
	list_filter = ('game',)

admin.site.register(Scenario, ScenarioAdmin)
admin.site.register(Country, CountryAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(GameArea, GameAreaAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Setup, SetupAdmin)
admin.site.register(Player, PlayerAdmin)
admin.site.register(Revolution, RevolutionAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(RetreatOrder, RetreatOrderAdmin)
admin.site.register(Letter, LetterAdmin)
admin.site.register(TurnLog, TurnLogAdmin)
