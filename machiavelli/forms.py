import django.forms as forms
from django.forms.formsets import BaseFormSet
from django.utils.safestring import mark_safe
from django.db.models import Q
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
	
	def __init__(self, user, **kwargs):
		super(GameForm, self).__init__(**kwargs)
		self.instance.created_by = user

	class Meta:
		model = Game
		fields = ('slug', 'scenario', 'time_limit')

class UnitForm(forms.ModelForm):
	type = forms.ChoiceField(required=True, choices=UNIT_TYPES)
    
	class Meta:
		model = Unit
		fields = ('type', 'area')
    
class SimpleOrderForm(forms.Form):
	orders = forms.CharField(required=True,
							help_text='Escribe las ordenes separadas por comas.')

def make_jsorder_form(player):
	all_units = Unit.objects.filter(player__game=player.game,
									#type__in=['A','F'],
									player__user__isnull=False)
	all_areas = player.game.gamearea_set.order_by('board_area__code')
	SUBCODES = (('H', _('Hold')),
				('-', _('Advance')),
				('=', _('Conversion')))
				#('B', _('Besiege')))
	class OrderForm(forms.Form):
		unit = forms.ModelChoiceField(queryset=player.unit_set.all())
		code = forms.ChoiceField(choices=ORDER_CODES, label='Order',
									widget=forms.Select(attrs={'onChange': 'changed_code(this)'}))
		destination = forms.ModelChoiceField(required=False, queryset=all_areas,
							#label='',
							widget=forms.Select(attrs={'style': 'display: none'}))
		conversion = forms.ChoiceField(choices=UNIT_TYPES,
							#label='',
							widget=forms.Select(attrs={'style': 'display: none'}))
		subunit = forms.ModelChoiceField(required=False, queryset=all_units,
							#label='',
							widget=forms.Select(attrs={'style': 'display: none'}))
		subcode = forms.ChoiceField(required=False, choices=SUBCODES,
									#label='',
									widget=forms.Select(attrs={'onChange': 'changed_subcode(this)',
									'style': 'display: none'}))
		subdestination = forms.ModelChoiceField(required=False, queryset=all_areas,
							#label='',
							widget=forms.Select(attrs={'style': 'display: none'}))
		subconversion = forms.ChoiceField(required=False, choices=UNIT_TYPES,
							#label='',
							widget=forms.Select(attrs={'style': 'display: none'}))
		
		
		def as_td(self):
			"Returns this form rendered as HTML <td>s -- excluding the <tr></tr>."
			tds = self._html_output(u'<td>%(errors)s %(field)s%(help_text)s</td>', u'<td style="width:10%">%s</td>', '</td>', u' %s', False)
			return u"<tr>%s</tr>" % tds

	return OrderForm

class BaseOrderFormSet(BaseFormSet):
	def as_row(self):
		forms = u' '.join([form.as_td() for form in self.forms])
		return mark_safe(u'\n'.join([unicode(self.management_form), forms]))

	def as_p(self):
		""" Returns this formset rendered as HTML <P>s."""
		forms = u' '.join([form.as_p() for form in self.forms])
		return mark_safe(u'\n'.join([unicode(self.management_form), forms]))
	
	def clean(self):
		if any(self.errors):
			return
		units = []
		for i in range(0, self.total_form_count()):
			form = self.forms[i]
			unit = form.cleaned_data['unit']
			if unit in units:
				raise forms.ValidationError, 'You cannot give a unit more than one order'
			units.append(unit)

def make_retreat_form(u):
	## possible_retreats includes all adjancent, non-standoff areas, and the
	## same area where the unit is located (convert to garrison)
	cond = Q(game=u.player.game)
	cond = cond & Q(standoff=False)
	cond = cond & Q(board_area__borders=u.area.board_area)
	## exclude the area where the attack came from
	cond = cond & ~Q(board_area__code__exact=u.must_retreat)
	## exclude areas with 'A' or 'F'
	cond = cond & ~Q(unit__type__in=['A','F'])
	## for armies, exclude seas
	if u.type == 'A':
		cond = cond & Q(board_area__is_sea=False)
	## for fleets, exclude areas that are adjacent but their coasts are not
	elif u.type == 'F':
		exclude = []
		for area in u.area.board_area.borders.all():
			if not area.is_adjacent(u.area.board_area, fleet=True):
				exclude.append(area.id)
		cond = cond & ~Q(board_area__id__in=exclude)
		## for fleets, exclude areas that are not seas or coasts
		cond = cond & ~Q(board_area__is_sea=False, board_area__is_coast=False)
	## add the own area if there is no garrison
	if u.area.board_area.is_fortified:
		if u.type == 'A' or (u.type == 'F' and u.area.board_area.has_port):
			try:
				Unit.objects.get(area=u.area, type='G')
			except:
				cond = cond | Q(id__exact=u.area.id)
	
	possible_retreats = GameArea.objects.filter(cond).distinct()
	
	class RetreatForm(forms.Form):
		unitid = forms.IntegerField(widget=forms.HiddenInput, initial=u.id)
		area = forms.ModelChoiceField(required=False,
							queryset=possible_retreats,
							empty_label='Disband unit',
							label=u)
	
	return RetreatForm

def make_reinforce_form(player):
	class ReinforceForm(forms.Form):
		type = forms.ChoiceField(required=True, choices=UNIT_TYPES)
		area = forms.ModelChoiceField(required=True,
					      queryset=player.get_areas_for_new_units(),
					      empty_label=None)

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

class LetterForm(forms.ModelForm):
	def __init__(self, sender, receiver, **kwargs):
		super(LetterForm, self).__init__(**kwargs)
		self.instance.sender = sender
		self.instance.receiver = receiver

	class Meta:
		model = Letter
		fields = ('body',)
