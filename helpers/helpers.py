from helpers.countries import Country
import pycountry
import gettext

german = gettext.translation('iso3166-1', pycountry.LOCALES_DIR, languages=['de'])
german.install()


def get_countries() -> list[Country]:
	"""
	Returns a list of Country objects representing all countries in pycountry.
	"""
	countries = []
	for country in pycountry.countries:
		countries.append(Country(_(country.name), country.alpha_2))
	return countries
