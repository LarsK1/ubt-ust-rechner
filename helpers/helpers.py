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
        self.responsible_for_shippment = False
        self.responsible_for_customs = False
        self.next_company: Handelsstufe | None = None
        self.previous_company: Handelsstufe | None = None
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
            return f"Zwischenhändler - {self.country}"

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

    def find_start_company(self):
        """
        Finds the start company in the chain transaction.
        """
        if self.previous_company:
            return self.previous_company.find_start_company()
        else:
            return self

    def find_end_company(self):
        """
        Finds the end company in the chain transaction.
        """
        if self.next_company:
            return self.next_company.find_end_company()
        else:
            return self

    def find_shipping_company(self):
        """
        Finds the shipping company in the chain transaction. Function only works, when started in the first company.
        """
        if self.responsible_for_shippment:
            return self
        elif self.next_company:
            return self.next_company.find_shipping_company()

    def find_custom_company(self):
        """
        Finds the custom handling company in the chain transaction. Function only works, when started in the first company.
        """
        if self.responsible_for_customs:
            return self
        elif self.next_company:
            return self.next_company.find_custom_company()


class Transaktion:
    """
    Represents a transaction in a chain transaction.
    """

    def __init__(self, start_company: Handelsstufe, end_company: Handelsstufe):
        self.start_company: Handelsstufe = start_company
        self.end_company: Handelsstufe = end_company
        self.shipping_company: Handelsstufe | None = None
        self.customs_company: Handelsstufe | None = None

    def find_shipping_company(self):
        """
        Finds the shipping company in the chain transaction.
        """
        self.shipping_company = self.start_company.find_shipping_company()
        return self.shipping_company

    def find_custom_company(self):
        self.customs_company = self.start_company.find_custom_company()
        return self.customs_company

    def get_ordered_chain_companies(self):
        """
        Returns the ordered chain companies.
        """
        companies = []
        current_company = self.start_company
        while current_company:
            companies.append(current_company)
            current_company = current_company.next_company
        return companies

    def includes_only_eu_countries(self):
        return all(company.country.EU for company in self.get_ordered_chain_companies())
