import pytest

from helpers.helpers import (
    Handelsstufe,
    Transaktion,
    Country,
    VatTreatmentType,
    IntermediaryStatus,
)

# --- Mock Country Data ---
# Annahme: Country(name, code, is_eu)
DE = Country("Deutschland", "DE")
AT = Country("Österreich", "AT")
FR = Country("Frankreich", "FR")
IT = Country("Italien", "IT")
PL = Country("Polen", "PL")
CH = Country("Schweiz", "CH")
US = Country("USA", "US")

# Mapping von Ländercodes zu Objekten für einfachen Zugriff in Tests
COUNTRIES = {
    "DE": DE,
    "AT": AT,
    "FR": FR,
    "PL": PL,
    "CH": CH,
    "US": US,
    "IT": IT,
}

# --- Testdaten-Struktur ---
TEST_SCENARIOS = [
    # --- Szenario 1: DE -> AT -> AT, A transportiert ---
    {
        "description": "DE -> AT -> AT (3 Firmen), A transportiert",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": True,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegt (da A transportiert), Ort DE (Start), Steuerfrei IG (DE->AT)
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # B -> C: Ruhend, Ort AT (Ende), Steuerpflichtig AT (AT->AT)
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "AT",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A braucht DE (für IG Supply)
            1: {"AT"},  # B braucht AT (für IG Erwerb und B->C)
            2: {"AT"},  # C braucht AT
        },
    },
    # --- Szenario 2: DE -> AT -> AT, C transportiert ---
    {
        "description": "DE -> AT -> AT (3 Firmen), C transportiert",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "AT",
                "ship": True,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },  # C transportiert
        ],
        "expected_deliveries": [
            # A -> B: Ruhend, Ort DE (Start), Steuerfrei IG (DE->AT)
            {
                "from": 0,
                "to": 1,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # B -> C: Bewegt (da C transportiert), Ort DE (Start), Steuerpflichtig DE (AT->AT, Ort DE)
            {
                "from": 1,
                "to": 2,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A braucht DE (für IG Supply)
            1: {"AT", "DE"},  # AT (für IG Erwerb)
            2: {"AT"},  # C braucht AT
        },
    },
    # --- Szenario 3: DE -> AT -> AT, B transportiert als Abnehmer ---
    {
        "description": "DE -> AT -> AT (3 Firmen), B transportiert als Abnehner",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": True,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.BUYER,
            },
            {
                "id": 2,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegt (da B als Lieferer auftritt), Ort DE (Start), Steuerfrei IG (DE->AT)
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # B -> C: Ruhend, Ort AT (Ende), Steuerpflichtig AT (AT->AT)
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "AT",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A braucht DE (für IG Supply)
            1: {
                "AT",
            },  # B braucht AT (für IG Erwerb von A und steuerbare Lief B->C in AT)
            2: {"AT"},  # C braucht AT
        },
    },
    # --- Szenario 4: DE -> AT -> AT, B transportiert als Lieferer ---
    {
        "description": "DE -> AT -> AT (3 Firmen), B transportiert als Lieferer",  # Beschreibung korrigiert
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": True,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.SUPPLIER,  # Status korrigiert
            },
            {
                "id": 2,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Ruhend, Ort DE (Start), Steuerpflichtig DE (DE->AT in DE)
            {
                "from": 0,
                "to": 1,
                "moved": False,  # Erwartung: Ruhend
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # B -> C: Bewegt (da B als Erwerber transportiert), Ort DE (Start), Steuerfrei IG (AT->AT, Ort DE, Ende AT)
            {
                "from": 1,
                "to": 2,
                "moved": True,  # Erwartung: Bewegt (korrigiert)
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,  # Erwartung: Steuerfrei IG (korrigiert)
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A braucht DE (für A->B)
            1: {"DE", "AT"},  # B braucht DE (für IG Supply B->C) und AT (home)
            2: {"AT"},  # C braucht AT (für IG Erwerb)
        },
    },
    # --- Szenario 5: AT -> FR -> IT (Dreieck), A transportiert ---
    {
        "description": "AT -> FR -> IT (Dreieck), A transportiert",
        "companies": [
            {
                "id": 0,
                "country_code": "AT",
                "ship": True,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },  # A transportiert
            {
                "id": 1,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "IT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegt (da A transportiert), Ort AT (Start), Steuerfrei IG (AT->FR)
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "AT",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # B -> C: Ruhend, Ort IT (Ende), RC da B(FR) an C(IT) in IT liefert
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "IT",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
        ],
        "expected_triangle": True,  # Sollte als Dreieck erkannt werden
        "expected_registrations": {  # Vereinfachte Registrierung!
            0: {"AT"},  # A nur in AT
            1: {"FR"},  # B nur in FR
            2: {"IT"},  # C nur in IT
        },
    },
    # --- NEU: Szenario 6: DE -> AT -> IT, A transportiert (Dreieck) ---
    {
        "description": "DE -> AT -> IT (Dreieck), A transportiert",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": True,  # A transportiert
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "IT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegt, Ort DE, Steuerfrei IG (DE->AT)
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # B -> C: Ruhend, Ort IT, RC (AT->IT in IT)
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "IT",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
        ],
        "expected_triangle": True,  # Dreiecksgeschäft
        "expected_registrations": {  # Vereinfachte Registrierung
            0: {"DE"},
            1: {"AT"},
            2: {"IT"},
        },
    },
    # --- Szenario 7: DE -> AT -> IT, B transportiert als Abnehmer ---
    {
        "description": "DE -> AT -> IT, B transportiert als Abnehmer",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": True,  # B transportiert
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.BUYER,  # als Abnehmer
            },
            {
                "id": 2,
                "country_code": "IT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # B -> C
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "IT",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
        ],
        "expected_triangle": True,
        "expected_registrations": {
            0: {"DE"},  # A braucht DE (für A->B)
            1: {
                "AT",
            },  # AT (home)
            2: {"IT"},  # C braucht IT (home)
        },
    },
    # --- Szenario 8: DE -> AT -> IT, C transportiert ---
    {
        "description": "DE -> AT -> IT, C transportiert",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "IT",
                "ship": True,  # C transportiert
                "customs": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Ruhend, Ort DE, Steuerpflichtig DE
            {
                "from": 0,
                "to": 1,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # B -> C: Bewegt, Ort DE, Steuerfrei IG (DE->IT)
            {
                "from": 1,
                "to": 2,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
        ],
        "expected_triangle": False,  # Kein Dreieck nach Vereinfachung
        "expected_registrations": {
            0: {"DE"},  # A braucht DE (für A->B)
            1: {
                "DE",
                "AT",
            },  # B braucht DE (A->B Erwerb & B->C Lief), AT (home), IT (B->C Erwerb)
            2: {"IT"},  # C braucht IT (home)
        },
    },
]


# --- Hilfsfunktion zum Erstellen der Kette ---
def create_company_chain(company_configs):
    """Erstellt eine Liste von Handelsstufe-Objekten und verknüpft sie."""
    companies = []
    max_identifier = len(company_configs)
    for config in company_configs:
        country = COUNTRIES[config["country_code"]]
        company = Handelsstufe(
            country=country, identifier=config["id"], max_identifier=max_identifier
        )
        company.responsible_for_shippment = config["ship"]
        company.responsible_for_customs = config["customs"]
        company.intermediary_status = config["intermediary_status"]

        if config["vat_change_code"]:
            company.set_changed_vat_id(COUNTRIES[config["vat_change_code"]])
        companies.append(company)

    # Verknüpfen
    for i in range(len(companies)):
        if i > 0:
            companies[i].previous_company = companies[i - 1]
        if i < len(companies) - 1:
            companies[i].next_company = companies[i + 1]

    return companies


# --- Der eigentliche Test ---
@pytest.mark.parametrize(
    "scenario", TEST_SCENARIOS, ids=[s["description"] for s in TEST_SCENARIOS]
)
def test_chain_transaction_scenarios(scenario):
    """
    Testet verschiedene Reihengeschäft-Szenarien.
    """
    print(
        f"\n--- Testing: {scenario['description']} ---"
    )  # Hilfreich bei der Ausführung

    # 1. Testdaten vorbereiten
    companies = create_company_chain(scenario["companies"])
    if not companies:
        pytest.fail("Fehler beim Erstellen der Firmenkette")
    start_company = companies[0]
    end_company = companies[-1]
    transaction = Transaktion(start_company, end_company)

    # 2. Berechnungen durchführen
    try:
        actual_deliveries = transaction.calculate_delivery_and_vat()
        actual_is_triangle = transaction.is_triangular_transaction()
        actual_registrations_raw = transaction.determine_registration_obligations()
    except ValueError as e:
        # Falls ein Fehler erwartet wird (z.B. kein Transporteur), hier prüfen
        # pytest.fail(f"Unerwarteter Fehler bei der Berechnung: {e}")
        # Wenn ein Fehler erwartet WIRD, müsste man das im Szenario definieren
        # und hier mit pytest.raises prüfen. Vorerst gehen wir von erfolgreicher Berechnung aus.
        pytest.fail(f"Berechnung fehlgeschlagen: {e}")

    # 3. Ergebnisse prüfen (Assertions)

    # a) Anzahl der Lieferungen
    assert len(actual_deliveries) == len(
        scenario["expected_deliveries"]
    ), "Anzahl der Lieferungen stimmt nicht"

    # b) Eigenschaften jeder Lieferung prüfen
    for i, expected_del in enumerate(scenario["expected_deliveries"]):
        actual_del = actual_deliveries[i]
        print(f"  Prüfe Lieferung {i+1}: {actual_del}")  # Debug-Ausgabe

        # Prüfe Lieferant und Kunde (optional, aber gut zur Sicherheit)
        assert (
            actual_del.lieferant.identifier == expected_del["from"]
        ), f"Lieferung {i+1}: Falscher Lieferant"
        assert (
            actual_del.kunde.identifier == expected_del["to"]
        ), f"Lieferung {i+1}: Falscher Kunde"

        # Prüfe Bewegt/Ruhend
        assert (
            actual_del.is_moved_supply == expected_del["moved"]
        ), f"Lieferung {i+1}: Status (bewegt/ruhend) falsch"

        # Prüfe Ort der Lieferung
        assert (
            actual_del.place_of_supply.code == expected_del["place"]
        ), f"Lieferung {i+1}: Ort der Lieferung falsch"

        # Prüfe Steuerbehandlung
        assert (
            actual_del.vat_treatment == expected_del["vat"]
        ), f"Lieferung {i+1}: Steuerbehandlung falsch"

    # c) Prüfung auf Dreiecksgeschäft
    assert (
        actual_is_triangle == scenario["expected_triangle"]
    ), "Erkennung Dreiecksgeschäft falsch"

    # d) Prüfung der Registrierungspflichten
    # Konvertiere das Ergebnis in ein vergleichbares Format (ID -> Set von Ländercodes)
    actual_registrations_formatted = {
        firma.identifier: {country.code for country in countries}
        for firma, countries in actual_registrations_raw.items()
    }
    expected_registrations_formatted = scenario["expected_registrations"]

    # Vergleiche die Dictionaries
    assert (
        actual_registrations_formatted == expected_registrations_formatted
    ), "Registrierungspflichten stimmen nicht überein"

    print("--- Test Passed ---")
