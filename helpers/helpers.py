import gettext
from enum import Enum, auto

import pycountry

from helpers.countries import Country

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


class VatTreatmentType(Enum):
    """Definiert mögliche umsatzsteuerliche Behandlungen einer Lieferung."""

    TAXABLE_NORMAL = auto()  # Steuerpflichtig, Lieferant schuldet USt
    TAXABLE_REVERSE_CHARGE = (
        auto()
    )  # Steuerpflichtig, Kunde schuldet USt (Reverse Charge)
    EXEMPT_IC_SUPPLY = auto()  # Steuerfrei (Innergemeinschaftliche Lieferung)
    EXEMPT_EXPORT = auto()  # Steuerfrei (Ausfuhr)
    NOT_TAXABLE = auto()  # Nicht steuerbar (im betrachteten Land)
    UNKNOWN = auto()


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
        # Behalte die ausführliche Repräsentation für Debugging etc. bei
        role = self.get_role_name()  # Nutze die neue Methode
        return f"{role} ({self.country.name} - {self.country.code})"

    def get_role_name(self, long_name=False) -> str:
        """Gibt einen kurzen Namen für die Rolle der Firma zurück."""
        if self.identifier == 0:
            return "Verkäufer"
        elif self.identifier == self.max_identifier - 1:
            return "Empfänger"
        else:
            # Unterscheidung zwischen erstem und weiteren Zwischenhändlern
            if self.identifier == 1:
                if long_name:
                    return "1. Zwischenhändler"
                return "1. ZH"
            else:
                if long_name:
                    return f"{self.identifier}. Zwischenhändler"
                return f"{self.identifier}. ZH"

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


class Lieferung:
    """
    Repräsentiert eine einzelne Lieferung innerhalb eines Reihengeschäfts.
    """

    def __init__(self, lieferant: Handelsstufe, kunde: Handelsstufe):
        self.lieferant = lieferant
        self.kunde = kunde
        self.is_moved_supply: bool = False
        self.place_of_supply: [Country] = None
        self.vat_treatment: VatTreatmentType = VatTreatmentType.UNKNOWN
        self.invoice_note: [str] = None  # Hinweis für die Rechnung

    def get_vat_treatment_display(self) -> str:
        """Gibt eine benutzerfreundliche Zeichenkette für die Steuerbehandlung zurück."""
        treatment = self.vat_treatment
        # Verwende Ländercode für Kürze, "?" wenn Ort unbekannt
        place_code = self.place_of_supply.code if self.place_of_supply else "?"

        if treatment == VatTreatmentType.TAXABLE_NORMAL:
            # Zeigt an, WO die Steuer anfällt
            return f"Steuerpflichtig ({place_code})"
        elif treatment == VatTreatmentType.TAXABLE_REVERSE_CHARGE:
            # Der Hinweis auf RC reicht meist, Ort ist implizit der des Kunden
            return f"Reverse Charge ({place_code})"
        elif treatment == VatTreatmentType.EXEMPT_IC_SUPPLY:
            return "Steuerfrei (IG)"
        elif treatment == VatTreatmentType.EXEMPT_EXPORT:
            return "Steuerfrei (Ausfuhr)"
        elif treatment == VatTreatmentType.NOT_TAXABLE:
            # Zeigt an, WO es nicht steuerbar ist
            return f"Nicht steuerbar ({place_code})"
        elif treatment == VatTreatmentType.UNKNOWN:
            return "Unbekannt"
        else:  # Fallback
            return treatment.name  # Gibt den Enum-Namen aus, falls neu hinzugefügt

    def __repr__(self):
        """Erzeugt eine kompakte und lesbare Darstellung der Lieferung."""
        # Kurze Darstellung für Lieferant und Kunde
        lieferant_repr = (
            f"{self.lieferant.get_role_name()} ({self.lieferant.country.code})"
        )
        kunde_repr = f"{self.kunde.get_role_name()} ({self.kunde.country.code})"

        # Status (Bewegt/Ruhend)
        status_repr = "Bewegt" if self.is_moved_supply else "Ruhend"

        # Ort (nur Ländercode)
        ort_repr = (
            f"Ort: {self.place_of_supply.code}" if self.place_of_supply else "Ort: ?"
        )

        # Kurze Steuerbehandlung
        vat_repr = self.get_vat_treatment_display()

        # Zusammenfügen mit Trennzeichen für Lesbarkeit
        return f"{lieferant_repr} -> {kunde_repr} | {status_repr} | {ort_repr} | {vat_repr}"

    def determine_place_of_supply(
        self, bewegte_lieferung, start_country: Country, end_country: Country
    ):
        """
        Bestimmt den Ort dieser Lieferung basierend darauf, welche Lieferung
        die bewegte ist und wo der Transport beginnt/endet.
        """
        bewegte_lieferung: Lieferung
        if self.is_moved_supply:
            # Ort der bewegten Lieferung ist dort, wo die Beförderung beginnt.
            self.place_of_supply = start_country
        else:
            # Prüfen, ob diese Lieferung VOR oder NACH der bewegten Lieferung liegt.
            current = self.kunde
            is_before = False
            while current is not None:
                # Wir prüfen, ob der *Kunde* dieser Lieferung der *Lieferant* der bewegten Lieferung ist
                # oder ob der *Lieferant* dieser Lieferung der *Lieferant* der bewegten Lieferung ist.
                # Das deckt den Fall ab, dass die bewegte Lieferung die erste ist.
                if (
                    current == bewegte_lieferung.lieferant
                    or self.lieferant == bewegte_lieferung.lieferant
                ):
                    is_before = True
                    break
                # Sicherheitscheck, um Endlosschleifen bei fehlerhafter Kette zu vermeiden
                if current == current.next_company:
                    raise ValueError(
                        f"Warnung: Endlosschleife in Kette bei {current} entdeckt."
                    )
                current = current.next_company

            if is_before:
                # Ruhende Lieferungen VOR der bewegten gelten als dort ausgeführt,
                # wo die Beförderung/Versendung beginnt.
                self.place_of_supply = start_country
            else:
                # Ruhende Lieferungen NACH der bewegten gelten als dort ausgeführt,
                # wo die Beförderung/Versendung endet.
                self.place_of_supply = end_country

        return self.place_of_supply

    def determine_vat_treatment(self, start_country: Country, end_country: Country):
        """
        Bestimmt die umsatzsteuerliche Behandlung dieser Lieferung.
        Muss NACH determine_place_of_supply aufgerufen werden.
        """
        if self.place_of_supply is None:
            self.vat_treatment = VatTreatmentType.UNKNOWN
            self.invoice_note = "Ort der Lieferung konnte nicht bestimmt werden."
            return

        # Vereinfachung: Wir gehen davon aus, dass "Steuerbarkeit" primär von der EU-Mitgliedschaft abhängt.
        # Eine Lieferung ist im Land des "place_of_supply" steuerbar, wenn dieses in der EU ist.
        # Detailliertere Prüfungen (z.B. § 1 UStG) sind hier nicht implementiert.

        is_place_in_eu = self.place_of_supply.EU
        is_supplier_in_eu = self.lieferant.country.EU
        is_customer_in_eu = self.kunde.country.EU
        is_start_in_eu = start_country.EU
        is_end_in_eu = end_country.EU

        # 1. Ist die Lieferung überhaupt im Land des Lieferorts steuerbar?
        if not is_place_in_eu:
            self.vat_treatment = VatTreatmentType.NOT_TAXABLE
            self.invoice_note = f"Nicht steuerbar (Ort: {self.place_of_supply.name})"
            return

        # 2. Prüfung auf Steuerbefreiungen (nur für die bewegte Lieferung relevant!)
        if self.is_moved_supply:
            # 2a. Innergemeinschaftliche Lieferung (§ 4 Nr. 1b, § 6a UStG)?
            # Bedingung: Ort im Inland (EU), Kunde in anderem EU-Staat, Transport endet dort, Kunde verwendet USt-Id.
            if (
                is_place_in_eu
                and is_customer_in_eu
                and self.place_of_supply.code != self.kunde.country.code
                and end_country.code == self.kunde.country.code
            ):
                # Annahme: Kunde verwendet gültige USt-Id des Ziellandes & Nachweise liegen vor.
                self.vat_treatment = VatTreatmentType.EXEMPT_IC_SUPPLY
                self.invoice_note = "Steuerfreie innergemeinschaftliche Lieferung"
                # Ggf. Hinweis auf § 6a UStG oder entspr. EU-Artikel
                return  # Befreit, keine weitere Prüfung nötig

            # 2b. Ausfuhrlieferung (§ 4 Nr. 1a, § 6 UStG)?
            # Bedingung: Ort im Inland (EU), Kunde im Drittland, Transport endet dort.
            if is_place_in_eu and not is_customer_in_eu and not is_end_in_eu:
                # Annahme: Ausfuhrnachweise liegen vor.
                self.vat_treatment = VatTreatmentType.EXEMPT_EXPORT
                self.invoice_note = "Steuerfreie Ausfuhrlieferung"
                # Ggf. Hinweis auf § 6 UStG oder entspr. EU-Artikel
                return  # Befreit, keine weitere Prüfung nötig

        # 3. Wenn steuerbar und nicht befreit: Wer schuldet die Steuer? (Reverse Charge?)
        # Prüfung auf Reverse Charge (§ 13b UStG / Art. 194 MwStSystRL)
        # Vereinfachter Fall: Leistungsempfänger im Inland (Ort der Lief.), leistender Unternehmer im Ausland.
        if (
            is_place_in_eu
            and self.place_of_supply.code
            == self.kunde.country.code  # Kunde sitzt im Land des Lieferorts
            and self.place_of_supply.code != self.lieferant.country.code
        ):  # Lieferant sitzt NICHT im Land des Lieferorts
            # Annahme: Kunde ist Unternehmer / jur. Person, die für Reverse Charge in Frage kommt.
            self.vat_treatment = VatTreatmentType.TAXABLE_REVERSE_CHARGE
            self.invoice_note = "Steuerschuldnerschaft des Leistungsempfängers"
            # Ggf. Hinweis auf § 13b UStG oder Art. 194 MwStSystRL
            return

        # 4. Standardfall: Steuerbar, nicht befreit, kein Reverse Charge
        self.vat_treatment = VatTreatmentType.TAXABLE_NORMAL
        self.invoice_note = f"Umsatzsteuerpflichtig in {self.place_of_supply.name}"

    # Hier müsste die Rechnung die USt des Landes von place_of_supply ausweisen.


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
        # Diese Methode ist jetzt weniger kritisch, da die Länder pro Lieferung geprüft werden,
        # aber kann für übergreifende Logik nützlich sein.
        return all(company.country.EU for company in self.get_ordered_chain_companies())

    def is_triangular_transaction(self) -> bool:
        """
        Prüft, ob die Bedingungen für ein (vereinfachtes) Dreiecksgeschäft vorliegen.

        Bedingungen (vereinfacht nach § 25b UStG / Art. 141 MwStSystRL):
        1. Drei Unternehmer (A, B, C).
        2. Alle in unterschiedlichen EU-Mitgliedstaaten registriert.
        3. Lieferung geht direkt von A an C. (Wird durch Reihengeschäft impliziert)
        4. B (mittlerer Unternehmer) verwendet für den Erwerb von A
           keine USt-IdNr. des Abgangslandes (A's Land).
        5. C (letzter Abnehmer) ist im Bestimmungsland für USt-Zwecke registriert. (Annahme hier)

        Returns:
                bool: True, wenn es sich wahrscheinlich um ein Dreiecksgeschäft handelt, sonst False.
        """
        firmen = self.get_ordered_chain_companies()

        # 1. Genau drei Unternehmer?
        if len(firmen) != 3:
            return False

        a = firmen[0]  # Erster Lieferer
        b = firmen[1]  # Mittlerer Unternehmer (Erwerber)
        c = firmen[2]  # Letzter Abnehmer

        # 2. Alle in der EU?
        if not (a.country.EU and b.country.EU and c.country.EU):
            return False

        # 3. Alle in unterschiedlichen EU-Mitgliedstaaten?
        if (
            a.country.code == b.country.code
            or b.country.code == c.country.code
            or a.country.code == c.country.code
        ):
            return False

        # 4. Verwendet B (Mittlerer) eine USt-Id des Abgangslandes (A)?
        #    Wenn B eine abweichende ID nutzt, darf es nicht die von A sein.
        if b.changed_vat and b.new_country:
            if b.new_country.code == a.country.code:
                # B tritt mit USt-Id des Abgangslandes auf -> KEIN Dreiecksgeschäft (i.S.d. Vereinfachung)
                return False
        # Wenn B keine abweichende ID nutzt (Standardfall), ist die Bedingung erfüllt.

        # Wenn alle Prüfungen bestanden wurden:
        return True

    def calculate_delivery_and_vat(self) -> list[Lieferung]:  # Umbenannt für Klarheit
        """
        Determines the moved/stationary supplies, their place of supply,
        and their VAT treatment within the chain transaction.

        Returns:
            List[Lieferung]: A list of Lieferung objects with determined
                             place_of_supply and vat_treatment.
        Raises:
            ValueError: If no shipping company is designated or other errors occur.
        """
        self.lieferungen = []
        bewegte_lieferung_gefunden = False
        bewegte_lieferung_obj: [Lieferung] = None

        # 1. Transporteur finden
        shipping_company = self.find_shipping_company()
        if shipping_company is None:
            raise ValueError("Keine Firma für den Transport verantwortlich gemacht.")

        # 2. Kette und Start-/Endland bestimmen
        firmen = self.get_ordered_chain_companies()
        if len(firmen) < 2:
            raise ValueError("Transaktion benötigt mindestens 2 Firmen.")
        start_country = firmen[
            0
        ].country  # Wo beginnt der Transport physisch? (Land des ersten Lieferanten)
        end_country = firmen[
            -1
        ].country  # Wo endet der Transport physisch? (Land des letzten Abnehmers)

        # 3. Alle Lieferungen erstellen
        for i in range(len(firmen) - 1):
            lieferant = firmen[i]
            kunde = firmen[i + 1]
            self.lieferungen.append(Lieferung(lieferant, kunde))

        # 4. Bewegte Lieferung zuordnen (§ 3 Abs. 6a UStG)
        # (Logik von vorher übernommen)
        if shipping_company == self.start_company:
            if self.lieferungen:
                self.lieferungen[0].is_moved_supply = True
                bewegte_lieferung_obj = self.lieferungen[0]
                bewegte_lieferung_gefunden = True
        elif shipping_company == self.end_company:
            if self.lieferungen:
                self.lieferungen[-1].is_moved_supply = True
                bewegte_lieferung_obj = self.lieferungen[-1]
                bewegte_lieferung_gefunden = True
        else:  # Zwischenhändler transportiert
            lieferung_vom_zh = next(
                (l for l in self.lieferungen if l.lieferant == shipping_company), None
            )
            lieferung_an_zh = next(
                (l for l in self.lieferungen if l.kunde == shipping_company), None
            )

            acts_as_supplier = False
            # Verwendet der ZH die USt-Id des Abgangslandes (Land seines Lieferanten)?
            # ODER: Hat er den Transport explizit im Auftrag seines Lieferanten durchgeführt? (Hier nicht prüfbar)
            # Wir nutzen die 'changed_vat'-Logik als Indikator für die Ausnahme
            if (
                shipping_company.changed_vat
                and lieferung_an_zh
                and shipping_company.new_country  # Sicherstellen, dass new_country gesetzt ist
                and shipping_company.new_country.code
                == lieferung_an_zh.lieferant.country.code
            ):
                acts_as_supplier = True

            if acts_as_supplier and lieferung_an_zh:
                lieferung_an_zh.is_moved_supply = True
                bewegte_lieferung_obj = lieferung_an_zh
                bewegte_lieferung_gefunden = True
            elif lieferung_vom_zh:
                lieferung_vom_zh.is_moved_supply = True
                bewegte_lieferung_obj = lieferung_vom_zh
                bewegte_lieferung_gefunden = True

        if not bewegte_lieferung_gefunden or bewegte_lieferung_obj is None:
            raise ValueError("Konnte die bewegte Lieferung nicht eindeutig zuordnen.")

        # 5. Ort der Lieferung UND Steuerbehandlung für alle Lieferungen bestimmen
        for lief in self.lieferungen:
            lief.determine_place_of_supply(
                bewegte_lieferung_obj, start_country, end_country
            )
            # Nach Bestimmung des Ortes die Steuerbehandlung ermitteln
            lief.determine_vat_treatment(start_country, end_country)

        return self.lieferungen
