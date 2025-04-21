from helpers.country_data import flags

EU = (
    "AT",
    "BE",
    "BG",
    "HR",
    "CZ",
    "CY",
    "DK",
    "EE",
    "FI",
    "FR",
    "DE",
    "GR",
    "HU",
    "IE",
    "IT",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SK",
    "SI",
    "ES",
    "SE",
)


class Country:
    def __init__(self, name, code):
        self.name = name
        self.code = code
        try:
            self.flag = flags[self.code]
        except KeyError:
            self.flag = None
        if self.code in EU:
            self.EU = True
        else:
            self.EU = False

    def __repr__(self):
        return f"{self.name} ({self.code})"

    def __eq__(self, country):
        if self.name == country.name and self.code == country.code:
            return True
        else:
            return False

    def __hash__(self):
        return hash((self.name, self.code))