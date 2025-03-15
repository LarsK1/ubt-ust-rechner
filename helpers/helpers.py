from helpers.countries import Country
import pycountry
import gettext

german = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["de"])
german.install()


def get_countries() -> list[Country]:
    """
    Returns a list of Country objects representing all countries in pycountry.
    """
    countries = []
    for country in pycountry.countries:
        countries.append(Country(_(country.name), country.alpha_2))
    return countries


class Handelsstufe:
    """
    Represents a company in a chain transaction.
    """

    def __init__(self, country: Country, identifier: int = 0, max_identifier: int = 0):
        self.country = country
        self.is_reciever = False
        self.is_supplier = False
        self.responsible_for_customs = False
        self.next_company: list[Handelsstufe] = []
        self.previous_company: list[Handelsstufe] = []
        self.identifier = identifier
        self.max_identifier = max_identifier
        if self.identifier > max_identifier:
            raise ValueError(
                "The identifier must be less than or equal to the max_identifier."
            )
        self.changed_vat = False
        self.new_country: Country = None

    def __repr__(self):
        if self.identifier == 0:
            return f"Verkäufer - {self.country}"
        elif self.identifier == self.max_identifier - 1:
            return f"Empfänger - {self.country}"
        else:
            return f"Handelsstufe - {self.country}"

    def add_previous_company_to_chain(self, company, previous_company):
        """
        Adds a company to a chain transaction.
        """
        company.previous_company = previous_company
        previous_company.next_company = company
        return company

    def add_next_company_to_chain(self, company, next_company):
        """
        Adds a company to a chain transaction.
        """
        company.next_company = next_company
        next_company.previous_company = company
        return company

    def set_changed_vat_id(self, new_country: Country):
        """
        Sets the new country for the company.
        """
        self.new_country = new_country
        self.changed_vat = True
        return self
