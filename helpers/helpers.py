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
        self.next_company: [Handelsstufe] = None  # Type Hint hinzugefügt
        self.previous_company: [Handelsstufe] = None  # Type Hint hinzugefügt
        self.identifier = identifier
        self.max_identifier = max_identifier
        if self.identifier > max_identifier:
            raise ValueError(
                "The identifier must be less than or equal to the max_identifier."
            )
        self.changed_vat = False
        self.new_country: [Country] = None  # Type Hint hinzugefügt

    def __repr__(self):
        if self.identifier == 0:
            return f"Verkäufer ({self.country})"  # Klammern für Klarheit
        elif self.identifier == self.max_identifier - 1:
            return f"Empfänger ({self.country})"  # Klammern für Klarheit
        else:
            # Unterscheidung zwischen erstem und weiteren Zwischenhändlern für Klarheit
            if self.identifier == 1:
                return f"1. Zwischenhändler ({self.country})"
            else:
                return f"{self.identifier}. Zwischenhändler ({self.country})"

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
        # Fallback, falls keine Firma explizit markiert ist (sollte nicht passieren bei korrekter Eingabe)
        elif (
            not self.previous_company
        ):  # Nur wenn wir beim Start sind und nichts gefunden wurde
            return None
        else:  # Sollte nicht erreicht werden, wenn von Start aus aufgerufen
            return None

    def find_custom_company(self):
        """
        Finds the custom handling company in the chain transaction. Function only works, when started in the first company.
        """
        if self.responsible_for_customs:
            return self
        elif self.next_company:
            return self.next_company.find_custom_company()
        # Fallback
        elif not self.previous_company:
            return None
        else:
            return None


# NEUE KLASSE: Lieferung
class Lieferung:
    """
    Repräsentiert eine einzelne Lieferung innerhalb eines Reihengeschäfts.
    """

    def __init__(self, lieferant: Handelsstufe, kunde: Handelsstufe):
        self.lieferant = lieferant
        self.kunde = kunde
        self.is_moved_supply: bool = False  # Ist dies die bewegte Lieferung?
        self.place_of_supply: [Country] = (
            None  # Ort der Lieferung (wird später bestimmt)
        )
        # Weitere Attribute könnten sein: Steuerbehandlung (steuerbar, steuerfrei etc.)

    def __repr__(self):
        bewegt_status = (
            "Bewegte Lieferung" if self.is_moved_supply else "Ruhende Lieferung"
        )
        return f"Lieferung von {self.lieferant} an {self.kunde} ({bewegt_status})"

    def determine_place_of_supply(self, bewegte_lieferung: "Lieferung"):
        """
        Bestimmt den Ort dieser Lieferung basierend darauf, welche Lieferung
        die bewegte ist.
        """
        if self.is_moved_supply:
            # Ort der bewegten Lieferung ist dort, wo die Beförderung beginnt.
            self.place_of_supply = self.lieferant.country
        else:
            # Prüfen, ob diese Lieferung VOR oder NACH der bewegten Lieferung liegt.
            # Dazu gehen wir von dieser Lieferung rückwärts/vorwärts bis zum Start/Ende
            # oder bis wir auf die bewegte Lieferung stoßen.

            # Prüfung: Liegt diese Lieferung VOR der bewegten?
            current = self.kunde
            is_before = False
            while current is not None:
                if current == bewegte_lieferung.lieferant:
                    is_before = True
                    break
                current = current.next_company

            if is_before:
                # Ruhende Lieferungen VOR der bewegten gelten als dort ausgeführt,
                # wo die Beförderung/Versendung beginnt (Ort des ersten Lieferanten).
                self.place_of_supply = (
                    bewegte_lieferung.lieferant.country
                )  # Oder: self.lieferant.country
            else:
                # Ruhende Lieferungen NACH der bewegten gelten als dort ausgeführt,
                # wo die Beförderung/Versendung endet (Ort des letzten Abnehmers).
                # Finde den Endkunden der gesamten Transaktion
                end_kunde_transaktion = self.lieferant.find_end_company()
                self.place_of_supply = (
                    end_kunde_transaktion.country
                )  # Oder: self.kunde.country

        return self.place_of_supply


class Transaktion:
    """
    Represents a transaction in a chain transaction.
    """

    def __init__(self, start_company: Handelsstufe, end_company: Handelsstufe):
        self.start_company: Handelsstufe = start_company
        self.end_company: Handelsstufe = end_company
        self.shipping_company: [Handelsstufe] = (
            None  # Wird in find_shipping_company gesetzt
        )
        self.customs_company: [Handelsstufe] = (
            None  # Wird in find_custom_company gesetzt
        )
        self.lieferungen: list[Lieferung] = (
            []
        )  # Liste der Lieferungen in dieser Transaktion

    def find_shipping_company(self) -> [Handelsstufe]:
        """
        Finds the shipping company in the chain transaction.
        Iterative approach starting from the start_company.
        """
        current_company = self.start_company
        while current_company:
            if current_company.responsible_for_shippment:
                self.shipping_company = current_company
                return self.shipping_company
            current_company = current_company.next_company
        self.shipping_company = None  # Explizit None setzen, wenn keine gefunden wurde
        return None

    def find_custom_company(self) -> [Handelsstufe]:
        """
        Finds the custom handling company in the chain transaction.
        Iterative approach starting from the start_company.
        """
        current_company = self.start_company
        while current_company:
            if current_company.responsible_for_customs:
                self.customs_company = current_company
                return self.customs_company
            current_company = current_company.next_company
        self.customs_company = None  # Explizit None setzen, wenn keine gefunden wurde
        return None

    def get_ordered_chain_companies(self) -> list[Handelsstufe]:
        """
        Returns the ordered chain companies.
        """
        companies = []
        current_company = self.start_company
        while current_company:
            companies.append(current_company)
            current_company = current_company.next_company
        return companies

    def includes_only_eu_countries(self) -> bool:
        """Checks if all companies in the chain are located in the EU."""
        return all(company.country.EU for company in self.get_ordered_chain_companies())

    def calculate_delivery(self) -> list[Lieferung]:
        """
        Determines the moved and stationary supplies within the chain transaction
        based on who is responsible for the shipment.

        Returns:
            List[Lieferung]: A list of Lieferung objects, where one is marked
                             as the moved supply (`is_moved_supply = True`).
        Raises:
            ValueError: If no shipping company is designated in the chain.
        """
        self.lieferungen = []  # Liste für diese Berechnung zurücksetzen
        bewegte_lieferung_gefunden = False

        # 1. Transporteur finden
        shipping_company = self.find_shipping_company()
        if shipping_company is None:
            # Hier könntest du auch eine Standardregel anwenden, aber eine Ausnahme ist sicherer
            raise ValueError(
                "Keine Firma für den Transport verantwortlich gemacht. Zuordnung der bewegten Lieferung nicht möglich."
            )

        # 2. Alle Lieferungen erstellen (noch ohne Zuordnung bewegt/ruhend)
        firmen = self.get_ordered_chain_companies()
        for i in range(len(firmen) - 1):
            lieferant = firmen[i]
            kunde = firmen[i + 1]
            self.lieferungen.append(Lieferung(lieferant, kunde))

        # 3. Bewegte Lieferung zuordnen (§ 3 Abs. 6a UStG)
        bewegte_lieferung_obj: [Lieferung] = None

        if shipping_company == self.start_company:
            # Fall 1: Erster Lieferer transportiert -> Lieferung L1 -> K1 ist bewegt
            if self.lieferungen:
                self.lieferungen[0].is_moved_supply = True
                bewegte_lieferung_obj = self.lieferungen[0]
                bewegte_lieferung_gefunden = True
        elif shipping_company == self.end_company:
            # Fall 2: Letzter Abnehmer transportiert -> Lieferung L(n-1) -> K(n) ist bewegt
            if self.lieferungen:
                self.lieferungen[-1].is_moved_supply = True
                bewegte_lieferung_obj = self.lieferungen[-1]
                bewegte_lieferung_gefunden = True
        else:
            # Fall 3: Ein Zwischenhändler (ZH) transportiert
            # Grundregel: Vermutung, dass ZH als Abnehmer handelt.
            # -> Lieferung VOM ZH an SEINEN KUNDEN ist die bewegte Lieferung.
            # Ausnahme (§ 3 Abs. 6a Satz 4 Halbsatz 2 UStG):
            #   Wenn ZH nachweist, dass er als Lieferer handelt (z.B. USt-IdNr. des Abgangslandes verwendet),
            #   dann ist die Lieferung AN IHN die bewegte Lieferung.

            # Finde die Lieferung VOM Zwischenhändler (shipping_company)
            lieferung_vom_zh = next(
                (l for l in self.lieferungen if l.lieferant == shipping_company), None
            )

            # Finde die Lieferung AN den Zwischenhändler (shipping_company)
            lieferung_an_zh = next(
                (l for l in self.lieferungen if l.kunde == shipping_company), None
            )

            # --- HIER Logik für die Ausnahme einfügen ---
            # Beispielhafte Prüfung (muss an deine genauen Kriterien angepasst werden):
            # Verwendet der ZH die USt-Id des Abgangslandes (also des Landes seines Lieferanten)?
            acts_as_supplier = False
            if (
                shipping_company.changed_vat
                and lieferung_an_zh
                and shipping_company.new_country == lieferung_an_zh.lieferant.country
            ):
                acts_as_supplier = True
            # --- Ende Ausnahme-Logik ---

            if acts_as_supplier and lieferung_an_zh:
                # Ausnahme trifft zu: Lieferung AN den ZH ist bewegt
                lieferung_an_zh.is_moved_supply = True
                bewegte_lieferung_obj = lieferung_an_zh
                bewegte_lieferung_gefunden = True
            elif lieferung_vom_zh:
                # Grundregel: Lieferung VOM ZH ist bewegt
                lieferung_vom_zh.is_moved_supply = True
                bewegte_lieferung_obj = lieferung_vom_zh
                bewegte_lieferung_gefunden = True

        if not bewegte_lieferung_gefunden:
            # Sollte durch die Logik oben eigentlich nicht passieren, aber als Sicherheitsnetz
            raise ValueError("Konnte die bewegte Lieferung nicht eindeutig zuordnen.")

        # 4. Ort der Lieferung für alle Lieferungen bestimmen (optional hier, oder später)
        if bewegte_lieferung_obj:
            for lief in self.lieferungen:
                lief.determine_place_of_supply(bewegte_lieferung_obj)

        return self.lieferungen
