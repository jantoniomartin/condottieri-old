from condottieri_events.models import *
from django.contrib import admin

class BaseEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season', 'phase')
	list_filter = ('game', 'year', 'season', 'phase')

class NewUnitEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year')
	list_filter = ('game', 'year')

class DisbandEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season', 'phase')
	list_filter = ('game', 'year', 'season', 'phase')

class OrderEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', 'country', '__unicode__', 'year', 'season')
	list_filter = ('game', 'country', 'year', 'season')

class StandoffEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season')
	list_filter = ('game', 'year', 'season')

class ConversionEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season', 'phase')
	list_filter = ('game', 'year', 'season', 'phase')

class ControlEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year')
	list_filter = ('game', 'year')

class MovementEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season', 'phase')
	list_filter = ('game', 'year', 'season', 'phase')

class RetreatEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season', 'phase')
	list_filter = ('game', 'year', 'season', 'phase')

class UnitEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season', 'phase')
	list_filter = ('game', 'year', 'season', 'phase', 'message')

class CountryEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season', 'phase')
	list_filter = ('game', 'year', 'season', 'phase', 'message')

class DisasterEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year', 'season', 'phase')
	list_filter = ('game', 'year', 'season', 'phase', 'message')

class IncomeEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year')
	list_filter = ('game', 'year')

class ExpenseEventAdmin(admin.ModelAdmin):
	ordering = ['-year']
	list_per_page = 20
	list_display = ('game', '__unicode__', 'year')
	list_filter = ('game', 'year')

admin.site.register(BaseEvent, BaseEventAdmin)
admin.site.register(NewUnitEvent, NewUnitEventAdmin)
admin.site.register(DisbandEvent, DisbandEventAdmin)
admin.site.register(OrderEvent, OrderEventAdmin)
admin.site.register(StandoffEvent, StandoffEventAdmin)
admin.site.register(ConversionEvent, ConversionEventAdmin)
admin.site.register(ControlEvent, ControlEventAdmin)
admin.site.register(MovementEvent, MovementEventAdmin)
admin.site.register(RetreatEvent, RetreatEventAdmin)
admin.site.register(UnitEvent, UnitEventAdmin)
admin.site.register(CountryEvent, CountryEventAdmin)
admin.site.register(DisasterEvent, DisasterEventAdmin)
admin.site.register(IncomeEvent, IncomeEventAdmin)
admin.site.register(ExpenseEvent, ExpenseEventAdmin)
