import django.forms as forms
from django.forms.formsets import BaseFormSet
from django.utils.safestring import mark_safe
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils.translation import ugettext_lazy as _

from machiavelli.models import *
import machiavelli.utils as utils

class GameForm(forms.ModelForm):
	slug = forms.SlugField(label=_("Slug"))
	scenario = forms.ModelChoiceField(queryset=Scenario.objects.filter(enabled=True),
									empty_label=None,
									cache_choices=True,
									label=_("Scenario"))
	time_limit = forms.ChoiceField(choices=TIME_LIMITS, label=_("Time limit"))
	visible = forms.BooleanField(required=False, label=_("Visible players?"))
	
	def __init__(self, user, **kwargs):
		super(GameForm, self).__init__(**kwargs)
		self.instance.created_by = user

	class Meta:
		model = Game
		fields = ('slug', 'scenario', 'time_limit', 'visible')

class ConfigurationForm(forms.ModelForm):
	def clean(self):
		cleaned_data = self.cleaned_data
		return cleaned_data
		if not cleaned_data['finances']:
			if cleaned_data['special_units']:
				cleaned_data['bribes'] = True
			if cleaned_data['assassinations'] or cleaned_data['lenders'] or cleaned_data['bribes']:
				cleaned_data['finances'] = True
		return cleaned_data

	class Meta:
		model = Configuration
		exclude = ('finances',
				'assassinations',
				'bribes',
				'special_units',
				'strategic',
				'lenders')

class UnitForm(forms.ModelForm):
	type = forms.ChoiceField(required=True, choices=UNIT_TYPES)
    
	class Meta:
		model = Unit
		fields = ('type', 'area')
    
def make_order_form(player):
	order_units = Order.objects.filter(unit__player=player).values_list('unit', flat=True)
	free_units = player.unit_set.exclude(id__in=order_units)
	all_units = Unit.objects.filter(player__game=player.game,
									player__user__isnull=False).order_by('area__board_area__name')
	all_areas = player.game.gamearea_set.order_by('board_area__code')
	
	class OrderForm(forms.ModelForm):
		unit = forms.ModelChoiceField(queryset=player.unit_set.all(), label=_("Unit"))
		code = forms.ChoiceField(choices=ORDER_CODES, label=_("Order"))
		destination = forms.ModelChoiceField(required=False, queryset=all_areas, label=_("Destination"))
		type = forms.ChoiceField(choices=UNIT_TYPES, label=_("Convert into"))
		subunit = forms.ModelChoiceField(required=False, queryset=all_units, label=_("Unit"))
		subcode = forms.ChoiceField(required=False, choices=ORDER_SUBCODES, label=_("Order"))
		subdestination = forms.ModelChoiceField(required=False, queryset=all_areas, label=_("Destination"))
		subtype = forms.ChoiceField(required=False, choices=UNIT_TYPES, label=_("Convert into"))
		
		def __init__(self, player, **kwargs):
			super(OrderForm, self).__init__(**kwargs)
			self.instance.player = player
		
		class Meta:
			model = Order
			fields = ('unit', 'code', 'destination', 'type',
					'subunit', 'subcode', 'subdestination', 'subtype')
		
		class Media:
			js = ("%smachiavelli/js/order_form.js" % settings.STATIC_URL,
				  "%smachiavelli/js/jquery.form.js" % settings.STATIC_URL)
			
		def clean(self):
			cleaned_data = self.cleaned_data
			unit = cleaned_data.get('unit')
			code = cleaned_data.get('code')
			destination = cleaned_data.get('destination')
			type = cleaned_data.get('type')
			subunit = cleaned_data.get('subunit')
			subcode = cleaned_data.get('subcode')
			subdestination = cleaned_data.get('subdestination')
			subtype = cleaned_data.get('subtype')
			
			## check if unit has already an order
			try:
				unit.order
			except:
				pass
			else:
				raise forms.ValidationError(_("This unit has already an order"))
			## check for errors
			if code == '-' and not destination:
				raise forms.ValidationError(_("You must select an area to advance into"))
			if code == '=':
				if not type:
					raise forms.ValidationError(_("You must select a unit type to convert into"))
				if unit.type == type:
					raise forms.ValidationError(_("A unit must convert into a different type"))
			if code == 'C':
				if not subunit:
					raise forms.ValidationError(_("You must select a unit to convoy"))
				if not subdestination:
					raise forms.ValidationError(_("You must select a destination area to convoy the unit"))
			if code == 'S':
				if not subunit:
					raise forms.ValidationError(_("You must select a unit to support"))
				if subcode == '-' and not subdestination:
					raise forms.ValidationError(_("You must select a destination area for the supported unit"))
				if subcode == '=':
					if not subtype:
						raise forms.ValidationError(_("You must select a unit type for the supported unit"))
					if subtype == subunit.type:
						raise forms.ValidationError(_("A unit must convert into a different type"))

			## set to None the fields that are not needed
			if code in ['H', '-', '=', 'B']:
				cleaned_data.update({'subunit': None,
									'subcode': None,
									'subdestination': None,
									'subtype': None})
				if code in ['H', '-', 'B']:
					cleaned_data.update({'type': None})
				if code in ['H', '=', 'B']:
					cleaned_data.update({'destination': None})
			elif code == 'C':
				cleaned_data.update({'destination': None,
									'type': None,
									'subcode': None,
									'subtype': None})
			else:
				cleaned_data.update({'destination': None,
									'type': None})
				if subcode in ['H', '-']:
					cleaned_data.update({'subtype': None})
				if subcode in ['H', '=']:
					cleaned_data.update({'subdestination': None})

			return cleaned_data
		
		def as_td(self):
			"Returns this form rendered as HTML <td>s -- excluding the <tr></tr>."
			tds = self._html_output(u'<td>%(errors)s %(field)s%(help_text)s</td>', u'<td style="width:10%%">%s</td>', '</td>', u' %s', False)
			return unicode(tds)
		
	return OrderForm

def make_retreat_form(u):
	possible_retreats = u.get_possible_retreats()
	
	class RetreatForm(forms.Form):
		unitid = forms.IntegerField(widget=forms.HiddenInput, initial=u.id)
		area = forms.ModelChoiceField(required=False,
							queryset=possible_retreats,
							empty_label='Disband unit',
							label=u)
	
	return RetreatForm

def make_reinforce_form(player, finances=False):
	if finances:
		unit_types = (('', '---'),) + UNIT_TYPES
		noarea_label = '---'
	else:
		unit_types = UNIT_TYPES
		noarea_label = None
	area_qs = player.get_areas_for_new_units(finances)

	class ReinforceForm(forms.Form):
		type = forms.ChoiceField(required=True, choices=unit_types)
		area = forms.ModelChoiceField(required=True,
					      queryset=area_qs,
					      empty_label=noarea_label)

		def clean(self):
			cleaned_data = self.cleaned_data
			type = cleaned_data.get('type')
			area = cleaned_data.get('area')
			if not type in area.possible_reinforcements():
				raise forms.ValidationError('This unit cannot be placed in this area')
			return cleaned_data

	return ReinforceForm

class BaseReinforceFormSet(BaseFormSet):
	def clean(self):
		if any(self.errors):
			return
		areas = []
		for i in range(0, self.total_form_count()):
			form = self.forms[i]
			if 'area' in form.cleaned_data:
				area = form.cleaned_data['area']
				if area in areas:
					print 'Two units in one area error'
					raise forms.ValidationError, 'You cannot place two units in the same area in one turn'
				areas.append(area)

def make_disband_form(player):
	class DisbandForm(forms.Form):
		units = forms.ModelMultipleChoiceField(required=True,
					      queryset=player.unit_set.all(),
					      label="Units to disband")
	return DisbandForm

def make_unit_payment_form(player):
	class UnitPaymentForm(forms.Form):
		units = forms.ModelMultipleChoiceField(required=True,
					      queryset=player.unit_set.filter(placed=True),
						  widget=forms.CheckboxSelectMultiple,
					      label="")
	return UnitPaymentForm


class LetterForm(forms.ModelForm):
	def __init__(self, sender, receiver, **kwargs):
		super(LetterForm, self).__init__(**kwargs)
		self.instance.sender = sender
		self.instance.receiver = receiver

	class Meta:
		model = Letter
		fields = ('body',)

def make_ducats_list(ducats):
	if ducats >= 3:
		items = ducats / 3 + 1
		ducats_list = ()
		for i in range(1, items):
			j = i * 3
			ducats_list += ((j,j),)
		print ducats_list
		return ducats_list
	else:
		return ((0, 0),)

def make_expense_form(player):
	ducats_list = make_ducats_list(player.ducats)
	unit_qs = Unit.objects.filter(player__game=player.game).order_by('area__board_area__code')
	area_qs = GameArea.objects.filter(game=player.game).order_by('board_area__code')

	class ExpenseForm(forms.ModelForm):
		ducats = forms.ChoiceField(required=True, choices=ducats_list)
		area = forms.ModelChoiceField(required=False, queryset=area_qs)
		unit = forms.ModelChoiceField(required=False, queryset=unit_qs)
	
		def __init__(self, player, **kwargs):
			super(ExpenseForm, self).__init__(**kwargs)
			self.instance.player = player
	
		class Meta:
			model = Expense
			fields = ('type', 'ducats', 'area', 'unit')
	
		def clean(self):
			cleaned_data = self.cleaned_data
			type = cleaned_data.get('type')
			ducats = cleaned_data.get('ducats')
			area = cleaned_data.get('area')
			unit = cleaned_data.get('unit')
	
			## temporarily disable rebellion related expenses
			if type in (1,2,3):
				raise forms.ValidationError(_("This expense is not yet implemented"))
			if type in (0,1,2,3):
				if not isinstance(area, GameArea):
					raise forms.ValidationError(_("You must choose an area"))
			elif type in (4,5,6,7,8,9):
				if not isinstance(unit, Unit):
					raise forms.ValidationError(_("You must choose a unit"))
			else:
				raise forms.ValidationError(_("Unknown expense"))
			## check that the minimum cost is paid
			cost = get_expense_cost(type, unit)
			if int(ducats) < cost:
				raise forms.ValidationError(_("You must pay at least %s ducats") % cost)
			## if famine relief, check if there is a famine marker
			if type == 0:
				if not area.famine:
					raise forms.ValidationError(_("There is no famine in this area"))
			## if disband or buy autonomous garrison, check if the unit is an autonomous garrison
			if type in (5, 6):
				if unit.type != 'G' or unit.player.country != None:
					raise forms.ValidationError(_("You must choose an autonomous garrison"))
			## checks for convert, disband or buy enemy units
			if type in (7, 8, 9):
				if unit.player == player:
					raise forms.ValidationError(_("You cannot choose one of your own units"))
				if unit.player.country == None:
					raise forms.ValidationError(_("You must choose an enemy unit"))
				if type == 7 and unit.type != 'G':
					raise forms.ValidationError(_("You must choose a non-autonomous garrison"))
			## check if bribing the unit is possible
			if type in (5,6,7,8,9):
				check_areas = unit.area.get_adjacent_areas(include_self=True)
				ok = False
				for a in check_areas:
					if a.player == player:
						ok = True
						break
				if not ok:
					check_ids = check_areas.values_list('id', flat=True)
					try:
						Unit.objects.get(player=player, area__id__in=check_ids)
					except MultipleObjectsReturned:
						## there is more than one unit
						ok = True
					except:
						## no units or any other exception
						ok = False
					else:
						## there is just one unit
						ok = True
				if not ok:
					raise forms.ValidationError(_("You cannot bribe this unit because it's too far from your units or areas"))
			return cleaned_data
	
	return ExpenseForm
