## Copyright (c) 2011 by Jose Antonio Martin <jantonio.martin AT gmail DOT com>
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU Affero General Public License as published by the
## Free Software Foundation, either version 3 of the License, or (at your option
## any later version.
##
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
## FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License
## for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/agpl.txt>.
##
## This license is also included in the file COPYING
##
## AUTHOR: Jose Antonio Martin <jantonio.martin AT gmail DOT com>

""" This module defines a paginator, inspired on django.core.paginator, that
paginates the Events by season and year.

"""

from django.utils.translation import ugettext_lazy as _

SEASONS = {
	1: _('Spring'),
	2: _('Summer'),
	3: _('Fall'),
}


class InvalidPage(Exception):
	pass

class SeasonNotAnInteger(InvalidPage):
	pass

class SeasonOutOfRange(InvalidPage):
	pass

class YearNotAnInteger(InvalidPage):
	pass

class EmptyPage(InvalidPage):
	pass

class SeasonPaginator(object):
	def __init__(self, object_list):
		self.object_list = object_list
		self._newest_year = self._oldest_year = None
		self._newest_season = None
		self._oldest_season = 1 ## oldest season is always spring

	def validate_date(self, year, season):
		""" Validates the combination of season and year. """
		try:
			season = int(season)
		except ValueError:
			raise SeasonNotAnInteger('The season number is not an integer')
		if not season in SEASONS.keys():
			raise SeasonOutOfRange('The season is out of range')
		try:
			year = int(year)
		except ValueError:
			raise YearNotAnInteger('The year is not an integer')
		if year > self.newest_year or (year == self.newest_year and season > self.newest_season):
			raise EmptyPage('The date is in the future')
		if year < self.oldest_year:
			raise EmptyPage('The date is in the past, out of scope')

		return year, season

	def page(self, year=None, season=None):
		"Returns a Page object for the given year and season."
		if year is None or season is None:
			year = self.newest_year
			season = self.newest_season
		else:
			year, season = self.validate_date(year, season)
		object_list = self.object_list.filter(year=year, season=season)
		if object_list.count() <= 0:
			raise EmptyPage('No events for this date.')
		return Page(object_list, year, season, self)

	def _get_newest_year(self):
		""" Returns the most recent year in the events queryset """
		if self._newest_year is None:
			try:
				self._newest_year = self.object_list[0].year
			except IndexError:
				pass
		return self._newest_year
	newest_year = property(_get_newest_year)

	def _get_oldest_year(self):
		""" Returns the oldest year in the events queryset """
		if self._oldest_year is None:
			try:
				self._oldest_year = self.object_list.reverse()[0].year
			except IndexError:
				pass
		return self._oldest_year
	oldest_year = property(_get_oldest_year)

	def _get_newest_season(self):
		""" Returns the most recent season in the events queryset """
		if self._newest_season is None:
			try:
				self._newest_season = self.object_list[0].season
			except IndexError:
				## there are no seasons yet
				pass
		return self._newest_season
	newest_season = property(_get_newest_season)

	def _get_oldest_season(self):
		""" Returns the oldest season in the events queryset """
		return self._oldest_season
	oldest_season = property(_get_oldest_season)

class Page(object):
	def __init__(self, object_list, year, season, paginator):
		self.object_list = object_list
		self.year = year
		self.season = season
		self.paginator = paginator
		if season is not None:
			self.season_name = SEASONS[season]
		else:
			self.season_name = None

	def __repr__(self):
		return '<Page for %s %s>' % (self.year, self.season)

	def has_next(self):
		if self.year > self.paginator.oldest_year:
			return True
		if self.year == self.paginator.oldest_year and self.season > self.paginator.oldest_season:
			return True
		return False

	def has_previous(self):
		if self.year < self.paginator.newest_year:
			return True
		if self.year == self.paginator.newest_year and self.season < self.paginator.newest_season:
			return True
		return False

	def has_other_pages(self):
		return self.has_previous() or self.has_next()

	def next_date(self):
		""" Returns a string with GET parameters """
		if self.season in (3, 2):
			params = (self.year, self.season - 1)
		elif self.season == 1:
			params = (self.year - 1, 3)
		return "year=%s&season=%s" % params
	
	def previous_date(self):
		""" Returns a string with GET parameters """
		if self.season in (2, 1):
			params = (self.year, self.season + 1)
		elif self.season == 3:
			params = (self.year + 1, 1)
		return "year=%s&season=%s" % params

