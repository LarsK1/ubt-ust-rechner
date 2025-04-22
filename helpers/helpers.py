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

    OUT_OF_SCOPE = auto()  #
    TAXABLE_NORMAL = auto()  # Steuerpflichtig, Lieferant schuldet USt
    TAXABLE_REVERSE_CHARGE = (
        auto()
    )  # Steuerpflichtig, Kunde schuldet USt (Reverse Charge)
    EXEMPT_IC_SUPPLY = auto()  # Steuerfrei (Innergemeinschaftliche Lieferung)
    EXEMPT_EXPORT = auto()  # Steuerfrei (Ausfuhr)
    NOT_TAXABLE = auto()  # Nicht steuerbar (im betrachteten Land)
    UNKNOWN = auto()


class IntermediaryStatus(Enum):
    BUYER = auto()
    OCCURING_SUPPLIER = auto()


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
        self.intermediary_status: IntermediaryStatus | None = None
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
        role = self.get_role_name(True)  # Nutze die neue Methode
        base_repr = f"{role} ({self.country.name} - {self.country.code})"

        # --- NEU: Status hinzufügen, wenn es ein Zwischenhändler mit Status ist ---
        # Prüfen, ob es ein Zwischenhändler ist (Position > 0 und < max-1)
        is_intermediary = 0 < self.identifier < (self.max_identifier - 1)
        if is_intermediary and self.intermediary_status is not None:
            status_str = self.get_intermideary_status()  # Hole den deutschen String
            # Füge den Status in Klammern hinzu, wenn er nicht "Unbekannt" ist
            if status_str != "Unbekannt":
                base_repr += f" [Status: {status_str}]"
        # --- ENDE NEU ---

        # --- Optional: Abweichende USt-ID hinzufügen ---
        if self.changed_vat and self.new_country:
            base_repr += f" [USt-ID: {self.new_country.code}]"
        # --- ENDE Optional ---

        return base_repr

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

    def get_intermideary_status(self) -> str:
        """Gibt den Status des Zwischenhändlers als lesbaren String zurück."""
        match self.intermediary_status:
            case IntermediaryStatus.BUYER:
                return "Erwerber"
            case IntermediaryStatus.OCCURING_SUPPLIER:
                return "Auftretender Lieferer"
            case _:
                return "Unbekannt"

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
        elif treatment == VatTreatmentType.OUT_OF_SCOPE:
            return "Nicht steuerbar (außerhalb EU)"
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
        """Determines the VAT treatment based on supply type, place, and countries involved."""

        place = self.place_of_supply
        if place is None:
            self.vat_treatment = VatTreatmentType.UNKNOWN
            self.invoice_note = "Ort der Lieferung unbekannt"
            return

        # Nutze das Land der USt-ID, falls abweichend, sonst Heimatland
        lieferant_country = self.lieferant.country
        kunde_country = self.kunde.country

        # --- Moved Supply Logic ---
        if self.is_moved_supply:
            is_eu_transaction = place.EU and end_country.EU  # Grundprüfung EU

            # Prüfung auf Dreiecksgeschäft ---
            is_triangle = False
            # Stelle sicher, dass das Lieferungsobjekt eine Referenz zur Transaktion hat
            if hasattr(self, "transaction") and self.transaction:
                try:
                    # Rufe die Prüfmethode der Transaktion auf
                    is_triangle = self.transaction.is_triangular_transaction()
                except Exception as e:
                    # Optional: Fehler loggen, falls die Prüfung fehlschlägt
                    print(f"DEBUG: Fehler bei Prüfung auf Dreiecksgeschäft: {e}")
                    # Fahre fort, als wäre es kein Dreiecksgeschäft

            if is_eu_transaction and is_triangle:
                # Fall: Bewegte Lieferung im Rahmen eines vereinfachten Dreiecksgeschäfts (§ 25b UStG)
                # Diese ist IMMER eine steuerfreie innergemeinschaftliche Lieferung.
                self.vat_treatment = VatTreatmentType.EXEMPT_IC_SUPPLY
                # Spezifischer Rechnungshinweis
                self.invoice_note = "Steuerfreie innergem. Lieferung (Dreiecksgeschäft)"
                # Optional: Gesetzliche Referenz hinzufügen
                self.invoice_note += " gem. § 25b UStG / Art. 141 MwStSystRL"

            # --- Bestehende Logik für andere Fälle der bewegten Lieferung ---
            # (Nur ausführen, wenn es KEIN Dreiecksgeschäft ist oder nicht EU)
            elif is_eu_transaction:  # Standard EU-Fall (kein Dreieck)
                if (
                    lieferant_country.EU
                    and kunde_country.EU
                    and lieferant_country != kunde_country
                ):
                    # Standard Innergemeinschaftliche Lieferung prüfen
                    # Hier wird angenommen, dass der Kunde eine gültige USt-ID eines anderen EU-Landes verwendet.
                    # Eine detailliertere Prüfung der USt-ID des Kunden könnte hier sinnvoll sein.
                    self.vat_treatment = VatTreatmentType.EXEMPT_IC_SUPPLY
                    self.invoice_note = "Steuerfreie innergem. Lieferung (§ 6a UStG)"
                    # TODO: Ggf. Prüfung der USt-ID des Kunden hinzufügen (Herkunft, Gültigkeit)
                elif lieferant_country == kunde_country and place == lieferant_country:
                    # Lieferung innerhalb desselben EU-Landes
                    self.vat_treatment = VatTreatmentType.TAXABLE_NORMAL
                    self.invoice_note = f"Steuerpflichtig in {place.code}"
                else:
                    # Fallback für andere EU-Konstellationen (sollte genauer geprüft werden)
                    self.vat_treatment = VatTreatmentType.TAXABLE_NORMAL
                    self.invoice_note = (
                        f"Steuerpflichtig in {place.code} (Prüfung nötig)"
                    )

            elif place.EU and not end_country.EU:  # Export aus EU
                self.vat_treatment = VatTreatmentType.EXEMPT_EXPORT
                self.invoice_note = "Steuerfreie Ausfuhrlieferung (§ 6 UStG)"

            elif not place.EU:  # Lieferung startet außerhalb der EU
                self.vat_treatment = VatTreatmentType.OUT_OF_SCOPE
                self.invoice_note = f"Nicht steuerbar (außerhalb EU: {place.code})"
            # Ggf. weitere Fälle (z.B. Import) hier behandeln

        # --- Stationary Supply Logic ---
        else:  # Ruhende Lieferung
            if place.EU:
                # --- Bestehende Logik für ruhende Lieferungen ---
                # Prüfe auf Reverse Charge Möglichkeit (häufig bei ruhenden Lieferungen)
                # Vereinfachte Annahme: RC wenn Lieferant nicht im Lieferort ansässig, Kunde aber schon (oder dort registriert)
                # Eine genauere Prüfung (Unternehmerstatus etc.) wäre in der Praxis nötig.

                # Erneute Prüfung auf Dreieck für spezifischen Hinweis bei RC
                is_triangle_stationary_check = False
                if hasattr(self, "transaction") and self.transaction:
                    try:
                        is_triangle_stationary_check = (
                            self.transaction.is_triangular_transaction()
                        )
                    except:
                        pass  # Fehler hier ignorieren

                # Beispielhafte RC-Prüfung (vereinfacht)
                # Benötigt ggf. eine Methode wie self.kunde.is_registered_in(place) in Handelsstufe
                if (lieferant_country != place and kunde_country == place) or (
                    lieferant_country != place
                    and hasattr(self.kunde, "is_registered_in")
                    and self.kunde.is_registered_in(place)
                ):
                    self.vat_treatment = VatTreatmentType.TAXABLE_REVERSE_CHARGE
                    # Spezifischer Hinweis für die zweite Lieferung im Dreiecksgeschäft
                    if (
                        is_triangle_stationary_check
                        and self.kunde == self.transaction.end_company
                    ):
                        self.invoice_note = f"Reverse Charge (Dreiecksgeschäft, Steuerschuldner: Kunde in {place.code})"
                    else:
                        self.invoice_note = (
                            f"Reverse Charge (Steuerschuldner: Kunde in {place.code})"
                        )
                else:
                    # Standardfall: Steuerpflichtig im Lieferort
                    self.vat_treatment = VatTreatmentType.TAXABLE_NORMAL
                    self.invoice_note = f"Steuerpflichtig in {place.code}"
            else:  # Ort der ruhenden Lieferung ist außerhalb der EU
                self.vat_treatment = VatTreatmentType.OUT_OF_SCOPE
                self.invoice_note = f"Nicht steuerbar (außerhalb EU: {place.code})"

        # Fallback, falls keine Behandlung ermittelt wurde
        if self.vat_treatment == VatTreatmentType.UNKNOWN:
            self.invoice_note = "Steuerbehandlung konnte nicht ermittelt werden."


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

        # Stelle sicher, dass der Transporteur bekannt ist
        shipping_company = self.find_shipping_company()
        if shipping_company is None:
            # Wenn kein Transporteur definiert ist, kann es kein Dreiecksgeschäft sein
            # (oder die Analyse ist unvollständig)
            return False
        # 6. Wird der Transport von C (letzter Abnehmer) veranlasst?
        if shipping_company == c:
            # Wenn C transportiert -> KEIN vereinfachtes Dreiecksgeschäft
            return False

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

    def determine_registration_obligations(self) -> dict[Handelsstufe, set[Country]]:
        """
        Ermittelt die wahrscheinlichen EU-Umsatzsteuer-Registrierungspflichten
        für jede beteiligte Firma basierend auf den Lieferungen, unter
        Berücksichtigung der Vereinfachung für Dreiecksgeschäfte.

        Returns:
                dict[Handelsstufe, set[Country]]: Ein Dictionary, das jeder Firma
                                                                                  ein Set von Ländern zuordnet,
                                                                                  in denen eine Registrierung
                                                                                  wahrscheinlich notwendig ist.
        """
        registration_needs = {
            firma: set() for firma in self.get_ordered_chain_companies()
        }
        firmen = self.get_ordered_chain_companies()

        # Stelle sicher, dass Lieferungen berechnet wurden
        if not self.lieferungen:
            try:
                self.calculate_delivery_and_vat()
            except ValueError:
                # Wenn Berechnung fehlschlägt, können keine Pflichten ermittelt werden
                return registration_needs
        if not self.lieferungen:
            return registration_needs  # Immer noch leer, gib leeres Dict zurück

        # --- Sonderbehandlung für Dreiecksgeschäfte ---
        if self.is_triangular_transaction():
            # Bei Dreiecksgeschäften gelten vereinfachte Registrierungsregeln
            if (
                len(firmen) == 3
            ):  # Sollte immer der Fall sein, wenn is_triangular_transaction True ist
                a, b, c = firmen[0], firmen[1], firmen[2]

                # A (Erster Lieferer) muss in seinem Land (EU) registriert sein
                if a.country.EU:
                    registration_needs[a].add(a.country)

                # B (Mittlerer Unternehmer) muss NUR in seinem Land (EU) registriert sein
                # Die Vereinfachung erspart ihm die Registrierung in A's und C's Land
                if b.country.EU:
                    registration_needs[b].add(b.country)

                # C (Letzter Abnehmer) muss in seinem Land (EU) registriert sein (für Erwerb/RC)
                if c.country.EU:
                    registration_needs[c].add(c.country)

                # Für Dreiecksgeschäfte ist die Prüfung hier abgeschlossen
                return registration_needs
            else:
                # Fallback, sollte nicht passieren bei korrekter is_triangular_transaction Logik
                pass  # Fährt mit Standardlogik fort, was aber bei Dreiecksgeschäft falsch wäre

        # --- Standard-Logik (wenn KEIN Dreiecksgeschäft vorliegt) ---
        # Grundannahme: Jede EU-Firma ist in ihrem Heimatland registriert
        for firma in registration_needs.keys():
            if firma.country.EU:
                registration_needs[firma].add(firma.country)

        # Gehe jede Lieferung durch und prüfe auf Registrierungspflichten
        lief: Lieferung
        for lief in self.lieferungen:
            lieferant = lief.lieferant
            kunde = lief.kunde
            place = lief.place_of_supply
            treatment = lief.vat_treatment

            # Überspringe, wenn kein Lieferort bestimmt oder außerhalb EU (Fokus auf EU)
            if not place or not place.EU:
                continue

            # 1. Pflichten des Lieferanten (lieferant)
            if treatment == VatTreatmentType.TAXABLE_NORMAL:
                # Lieferant muss Steuer im Lieferort-Land abführen -> Registrierung nötig
                registration_needs[lieferant].add(place)
            elif treatment == VatTreatmentType.EXEMPT_IC_SUPPLY:
                # Lieferant muss IG-Lieferung melden -> Registrierung im Abgangsland (place) nötig
                registration_needs[lieferant].add(place)
            elif treatment == VatTreatmentType.EXEMPT_EXPORT:
                # Lieferant muss Ausfuhr nachweisen -> Registrierung im Abgangsland (place) nötig
                registration_needs[lieferant].add(place)
            # Bei TAXABLE_REVERSE_CHARGE hat der Lieferant i.d.R. keine *zusätzliche* Registrierungspflicht *nur* wegen dieser Lieferung im Zielland

            # 2. Pflichten des Kunden (kunde)
            # Kunde tätigt innergem. Erwerb (bei EXEMPT_IC_SUPPLY an ihn) ODER
            # schuldet Steuer im Empfangsland (bei TAXABLE_REVERSE_CHARGE)
            if (
                treatment == VatTreatmentType.EXEMPT_IC_SUPPLY
                or treatment == VatTreatmentType.TAXABLE_REVERSE_CHARGE
            ):
                # Kunde muss im Land des Erwerbs / der RC-Leistung registriert sein.
                # Das ist i.d.R. das 'place_of_supply' der RC-Leistung oder das Land des Kunden beim Erwerb.
                # Wir nehmen hier vereinfacht an, dass 'place' relevant ist.
                if kunde.country.EU:  # Nur relevant für EU-Kunden
                    registration_needs[kunde].add(place)

        return registration_needs

    def calculate_delivery_and_vat(self) -> list[Lieferung]:  # Umbenannt für Klarheit
        """
        Determines the moved/stationary supplies, their place of supply,
        and their VAT treatment within the chain transaction. Incorporates
        the intermediary status according to § 3 Abs. 6a S. 4 UStG.

        Returns:
            List[Lieferung]: A list of Lieferung objects with determined
                             place_of_supply and vat_treatment.
        Raises:
            ValueError: If no shipping company is designated or other errors occur.
        """
        self.lieferungen = []
        bewegte_lieferung_gefunden = False
        bewegte_lieferung_obj: Lieferung | None = None  # Type hint angepasst

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
        if not self.lieferungen:  # Sicherstellen, dass Lieferungen existieren
            raise ValueError("Keine Lieferungen in der Transaktion vorhanden.")

        if shipping_company == self.start_company:
            # Fall 1: Erster Lieferant transportiert -> Lieferung 1 ist bewegt
            self.lieferungen[0].is_moved_supply = True
            bewegte_lieferung_obj = self.lieferungen[0]
            bewegte_lieferung_gefunden = True
        elif shipping_company == self.end_company:
            # Fall 2: Letzter Abnehmer transportiert -> Letzte Lieferung ist bewegt
            self.lieferungen[-1].is_moved_supply = True
            bewegte_lieferung_obj = self.lieferungen[-1]
            bewegte_lieferung_gefunden = True
        else:  # Fall 3: Zwischenhändler transportiert
            # Finde die Lieferung AN den transportierenden Zwischenhändler
            lieferung_an_zh = next(
                (l for l in self.lieferungen if l.kunde == shipping_company), None
            )
            # Finde die Lieferung VOM transportierenden Zwischenhändler
            lieferung_vom_zh = next(
                (l for l in self.lieferungen if l.lieferant == shipping_company), None
            )

            # Priorität: Explizit gesetzter Status des Zwischenhändlers
            if (
                shipping_company.intermediary_status
                == IntermediaryStatus.OCCURING_SUPPLIER
            ):
                # Status "Auftretender Lieferer": Lieferung AN den ZH ist bewegt (§ 3 Abs. 6a S. 4 Alt. 2 UStG)
                if lieferung_an_zh:
                    lieferung_an_zh.is_moved_supply = True
                    bewegte_lieferung_obj = lieferung_an_zh
                    bewegte_lieferung_gefunden = True
                else:
                    # Sollte nicht passieren, wenn die Kette korrekt ist
                    raise ValueError(
                        f"Konnte Lieferung an transportierenden Zwischenhändler {shipping_company} nicht finden."
                    )

            elif shipping_company.intermediary_status == IntermediaryStatus.BUYER:
                # Status "Erwerber": Lieferung VOM ZH ist bewegt (§ 3 Abs. 6a S. 4 Alt. 1 UStG)
                if lieferung_vom_zh:
                    lieferung_vom_zh.is_moved_supply = True
                    bewegte_lieferung_obj = lieferung_vom_zh
                    bewegte_lieferung_gefunden = True
                else:
                    # Sollte nicht passieren
                    raise ValueError(
                        f"Konnte Lieferung vom transportierenden Zwischenhändler {shipping_company} nicht finden."
                    )

            else:  # Priorität 2: Status "Nicht festgelegt" (None) -> Prüfung der USt-ID (§ 3 Abs. 6a S. 4 UStG)
                # Prüfe, ob der Zwischenhändler die USt-ID des Abgangslandes verwendet
                if (
                    shipping_company.changed_vat
                    and shipping_company.new_country
                    and shipping_company.new_country.code == start_country.code
                ):
                    # Fall: ZH verwendet USt-ID des Abgangslandes -> Lieferung AN ZH ist bewegt (wie "Auftretender Lieferer")
                    if lieferung_an_zh:
                        lieferung_an_zh.is_moved_supply = True
                        bewegte_lieferung_obj = lieferung_an_zh
                        bewegte_lieferung_gefunden = True
                    else:
                        raise ValueError(
                            f"Konnte Lieferung an transportierenden Zwischenhändler {shipping_company} (mit USt-ID von {start_country.code}) nicht finden."
                        )
                else:
                    # Fall: ZH verwendet eigene USt-ID oder die eines anderen Landes (NICHT Abgangsland)
                    # -> Regelvermutung: Lieferung VOM ZH ist bewegt (wie "Erwerber")
                    if lieferung_vom_zh:
                        lieferung_vom_zh.is_moved_supply = True
                        bewegte_lieferung_obj = lieferung_vom_zh
                        bewegte_lieferung_gefunden = True
                    else:
                        raise ValueError(
                            f"Konnte Lieferung vom transportierenden Zwischenhändler {shipping_company} nicht finden."
                        )

        if not bewegte_lieferung_gefunden or bewegte_lieferung_obj is None:
            # Dieser Fehler sollte durch die obigen Prüfungen eigentlich nicht mehr auftreten
            raise ValueError("Konnte die bewegte Lieferung nicht eindeutig zuordnen.")

        # 5. Ort der Lieferung UND Steuerbehandlung für alle Lieferungen bestimmen
        for lief in self.lieferungen:
            lief.determine_place_of_supply(
                bewegte_lieferung_obj, start_country, end_country
            )
            # Nach Bestimmung des Ortes die Steuerbehandlung ermitteln
            lief.determine_vat_treatment(start_country, end_country)

        return self.lieferungen
