import pytest

from helpers.helpers import (
    Handelsstufe,
    Transaktion,
    Country,
    VatTreatmentType,
    IntermediaryStatus,
)

# --- Mock Country Data ---
DE = Country("Deutschland", "DE")
AT = Country("Österreich", "AT")
FR = Country("Frankreich", "FR")
IT = Country("Italien", "IT")
PL = Country("Polen", "PL")
ES = Country("Spanien", "ES")  # NEU
BE = Country("Belgien", "BE")  # NEU
NL = Country("Niederlande", "NL")  # NEU
LU = Country("Luxemburg", "LU")  # NEU
IE = Country("Irland", "IE")  # NEU
CH = Country("Schweiz", "CH")
US = Country("USA", "US")
CN = Country("China", "CN")

# Mapping von Ländercodes zu Objekten für einfachen Zugriff in Tests
COUNTRIES = {
    "DE": DE,
    "AT": AT,
    "FR": FR,
    "PL": PL,
    "IT": IT,
    "ES": ES,
    "BE": BE,
    "NL": NL,
    "LU": LU,
    "IE": IE,
    "CH": CH,
    "US": US,
    "CN": CN,
}

# --- Testdaten-Struktur ---
TEST_SCENARIOS_THREE_COMPANIES = [
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
    # --- Szenario 6: DE -> AT -> IT, A transportiert (Dreieck) ---
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
    # --- Szenario 7: DE -> AT -> IT, B transportiert als Abnehmer (Dreieck) ---
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
    # --- Szenario 9: DE -> CN -> CN, A transportiert & Export ---
    {
        "description": "DE -> CN -> CN, A transportiert & Export",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": True,  # A transportiert
                "customs": True,  # A macht Export-Zoll
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegt, Ort DE, Steuerfrei Export
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_EXPORT,
            },
            # B -> C: Ruhend, Ort CN, Nicht EU-Steuerbar
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.TAXABLE_NORMAL,  # Eigentlich in CN steuerbar
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A braucht DE (Export)
            1: set(),  # B (CN) braucht keine EU-Reg.
            2: set(),  # C (CN) braucht keine EU-Reg.
        },
    },
    # --- Szenario 10: DE -> CN -> CN, B transportiert als Abnehmer & Export ---
    {
        "description": "DE -> CN -> CN, B transportiert als Abnehmer & Export",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": True,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "CN",
                "ship": True,  # B transportiert
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.BUYER,  # als Abnehmer
            },
            {
                "id": 2,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegte Lieferung, steuerbar in DE
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_EXPORT,
            },
            # B -> C: Ruhende Lieferung, Ort CN, in CN steuerbar
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.TAXABLE_NORMAL,  #  eigentlich in CN steuerbar
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A braucht DE (Lieferung in DE)
            1: set(),  # B (CN) braucht keine EU-Reg.
            2: set(),  # C (CN) braucht keine EU-Reg.
        },
    },
    # --- Szenario 11: DE -> DE -> CN, B(FR-ID) transportiert als Abnehmer & Export ---
    {
        "description": "DE -> DE -> CN, B(FR-ID) transportiert als Abnehmer & Export",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "DE",  # B sitzt in DE
                "ship": True,  # B transportiert
                "customs": True,  # B macht Export-Zoll
                "import_vat": False,
                "vat_change_code": "FR",  # B nutzt FR USt-ID
                "intermediary_status": IntermediaryStatus.BUYER,  # als Abnehmer
            },
            {
                "id": 2,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegte Lieferung, Ort DE, IG-Lieferung an FR
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_EXPORT,
            },
            # B -> C: Ruhende Lieferung, Ort DE, Steuerfrei Export
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A braucht DE
            1: {"DE", "FR"},  # B braucht DE (home, Export) und FR (USt-ID Nutzung)
            2: set(),  # C (CN) braucht keine EU-Reg.
        },
    },
    # --- Szenario 12: CN -> DE -> DE, A transportiert, A macht EUSt ---
    # (§ 3 Abs. 8 UStG sollte greifen -> Lieferort A->B wird DE)
    {
        "description": "CN -> DE -> DE, A transportiert, A macht EUSt",
        "companies": [
            {
                "id": 0,
                "country_code": "CN",
                "ship": True,  # A transportiert
                "customs": False,  # Export CH nicht relevant für EU-USt
                "import_vat": True,  # A macht EUSt in DE
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegt, Ort CH->DE (§3 Abs. 8), Steuerpflichtig DE (RC)
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",  # Ort verlagert nach DE
                "vat": VatTreatmentType.TAXABLE_NORMAL,  # A(CN) an B(DE) in DE -> RC
            },
            # B -> C: Ruhend, Ort DE (Ende Transport), Steuerpflichtig DE
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,  # B(DE) an C(DE) in DE -> Normal
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A (CN) braucht DE (wegen EUSt und Lieferung in DE)
            1: {"DE"},  # B braucht DE (für RC-Erwerb und Lieferung B->C)
            2: {"DE"},  # C braucht DE (home)
        },
    },
    # --- Szenario 13: DE -> DE -> CN, B transportiert ---
    {
        "description": "DE -> DE -> CN, B transportiert, B macht Zoll",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "DE",
                "ship": True,
                "customs": True,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Ruhend, Ort DE->DE
            {
                "from": 0,
                "to": 1,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # B -> C: Bewegte Lieferung, Steuerbar in DE
            {
                "from": 1,
                "to": 2,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_EXPORT,  # Export an C
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},
            1: {"DE"},  # wegen bewegte Lieferung keine Registrierungspflicht in CN
            2: set(),
        },
    },
    # --- Szenario 14: DE -> DE -> CN, A transportiert ---
    {
        "description": "DE -> DE -> CN, A transportiert, A macht Zoll",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": True,
                "customs": True,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Ruhend, Ort DE->DE
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_EXPORT,
            },
            # B -> C: Ruhende Lieferung, Steuerbar in CN
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,  # Export an C
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},
            1: {
                "DE",
            },  # wegen bewegte Lieferung keine Registrierungspflicht in CN
            2: set(),
        },
    },
]
TEST_SCENARIOS_FOUR_COMPANIES = [
    # --- Szenario 1: DE -> AT -> PL -> FR, A transportiert ---
    {
        "description": "4 Firmen: DE -> AT -> PL -> FR, A transportiert",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": True,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "import_vat": False,
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
            # B -> C: Ruhend, Ort FR,
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "FR",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # C -> D: Ruhend, Ort FR,
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "FR",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (IG Lief)
            1: {"AT", "FR"},  # B: AT (home, IG Erw), FR (RC Lief B->C)
            2: {"PL", "FR"},  # C: PL (home, IG Erw), FR (RC Lief C->D)
            3: {"FR"},  # D: FR (home, IG Erw)
        },
    },
    # --- Szenario 2: DE -> AT -> PL -> FR, D transportiert ---
    {
        "description": "4 Firmen: DE -> AT -> PL -> FR, D transportiert",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "FR",
                "ship": True,
                "customs": False,
                "import_vat": False,
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
            # B -> C: Ruhend, Ort DE, Steuerpflichtig DE
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # C -> D: Bewegt, Ort DE, Steuerfrei IG (DE->FR)
            {
                "from": 2,
                "to": 3,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (Lief A->B)
            1: {"AT", "DE"},  # B: AT (home), DE (Lief B->C)
            2: {"PL", "DE"},  # C: PL (home), DE (IG Lief C->D)
            3: {"FR"},  # D: FR (home, IG Erw)
        },
    },
    # --- Szenario 3: DE -> AT -> PL -> FR, B transportiert als Abnehmer ---
    {
        "description": "4 Firmen: DE -> AT -> PL -> FR, B transportiert als Abnehmer",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": True,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.BUYER,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "import_vat": False,
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
            # B -> C: Ruhend, Ort FR, RC (AT->PL in FR)
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "FR",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # C -> D: Ruhend, Ort FR, RC (PL->FR in FR)
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "FR",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
        ],
        "expected_triangle": False,  # Könnte als Dreieck A-B-C interpretiert werden, aber hier Standardlogik
        "expected_registrations": {
            0: {"DE"},  # A: DE (IG Lief)
            1: {"AT", "FR"},  # B: AT (home, IG Erw), FR (RC Lief B->C)
            2: {"PL", "FR"},  # C: PL (home, IG Erw), FR (RC Lief C->D)
            3: {"FR"},  # D: FR (home, IG Erw)
        },
    },
    # --- Szenario 4: DE -> AT -> PL -> FR, B transportiert als Lieferer ---
    {
        "description": "4 Firmen: DE -> AT -> PL -> FR, B transportiert als Lieferer",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": True,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.SUPPLIER,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "import_vat": False,
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
            # B -> C: Bewegt, Ort DE, Steuerfrei IG (DE->FR)
            {
                "from": 1,
                "to": 2,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # C -> D: Ruhend, Ort FR, RC (PL->FR in FR)
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "FR",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (Lief A->B)
            1: {"AT", "DE"},  # B: AT (home), DE (IG Lief B->C)
            2: {"PL", "FR"},  # C: PL (home, IG Erw), FR (RC Lief C->D)
            3: {"FR"},  # D: FR (home, IG Erw)
        },
    },
    # --- Szenario 5: DE -> AT -> PL -> FR, C transportiert als Abnehmer ---
    {
        "description": "4 Firmen: DE -> AT -> PL -> FR, C transportiert als Abnehmer",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": True,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.BUYER,
            },
            {
                "id": 3,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "import_vat": False,
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
            # B -> C: Bewegt, Ort DE, Steuerfrei IG (DE->PL)
            {
                "from": 1,
                "to": 2,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # C -> D: Ruhend, Ort FR, RC (PL->FR in FR)
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "FR",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (Lief A->B)
            1: {"AT", "DE"},  # B: AT (home), DE (IG Lief B->C)
            2: {"PL", "FR"},  # C: PL (home, IG Erw), FR (RC Lief C->D)
            3: {"FR"},  # D: FR (home, IG Erw)
        },
    },
    # --- Szenario 6: DE -> AT -> PL -> FR, C transportiert als Lieferer ---
    {
        "description": "4 Firmen: DE -> AT -> PL -> FR, C transportiert als Lieferer",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": True,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.SUPPLIER,
            },
            {
                "id": 3,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "import_vat": False,
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
            # B -> C: Ruhend, Ort DE, Steuerpflichtig DE
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # C -> D: Bewegt, Ort DE, Steuerfrei IG (DE->FR)
            {
                "from": 2,
                "to": 3,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (Lief A->B)
            1: {"AT", "DE"},  # B: AT (home), DE (Lief B->C)
            2: {"PL", "DE"},  # C: PL (home), DE (IG Lief C->D)
            3: {"FR"},  # D: FR (home, IG Erw)
        },
    },
    # --- Szenario 7: DE -> AT -> PL -> CN, A transportiert & Export ---
    {
        "description": "4 Firmen: DE -> AT -> PL -> CN, A transportiert & Export",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": True,
                "customs": True,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegt, Ort DE, Steuerfrei Export
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_EXPORT,
            },
            # B -> C: Ruhend, Ort CN, Nicht EU-Steuerbar
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,
            },
            # C -> D: Ruhend, Ort CN, Nicht EU-Steuerbar
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (Export)
            1: {"AT"},  # B: AT (home)
            2: {"PL"},  # C: PL (home)
            3: set(),  # D: CN
        },
    },
    # --- Szenario 8: DE -> AT -> PL -> CN, C transportiert als Abnehmer & Export ---
    {
        "description": "4 Firmen: DE -> AT -> PL -> CN, C transportiert als Abnehmer & Export",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": True,
                "customs": True,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.BUYER,
            },
            {
                "id": 3,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
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
            # B -> C: Bewegt, Ort DE, Steuerfrei Export
            {
                "from": 1,
                "to": 2,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_EXPORT,
            },
            # C -> D: Ruhend, Ort CN, Nicht EU-Steuerbar
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (Lief A->B)
            1: {"AT", "DE"},  # B: AT (home), DE (Export B->C)
            2: {"PL"},  # C: PL (home)
            3: set(),  # D: CN
        },
    },
    # --- Szenario 9: CN -> DE -> AT -> PL, A transportiert & EUSt (§3(8)) ---
    {
        "description": "4 Firmen: CN -> DE -> AT -> PL, A transportiert & EUSt (§3(8))",
        "companies": [
            {
                "id": 0,
                "country_code": "CN",
                "ship": True,
                "customs": False,
                "import_vat": True,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Bewegt, Ort DE (verlagert!), Steuerpflichtig DE (Normal, da A EUSt zahlt)
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "PL",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # B -> C: Ruhend, Ort PL, RC (DE->AT in PL)
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "PL",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # C -> D: Ruhend, Ort PL, Steuerpflichtig PL (AT->PL in PL)
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "PL",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (EUSt, Lief A->B)
            1: {"DE", "PL"},  # B: DE (home), PL (RC Lief B->C)
            2: {"AT", "PL"},  # C: AT (home, IG Erw), PL (Lief C->D)
            3: {"PL"},  # D: PL (home, IG Erw)
        },
    },
    # --- Szenario 10: CN -> DE -> AT -> PL, C transportiert als Abnehmer, A zahlt EUSt ---
    {
        "description": "4 Firmen: CN -> DE -> AT -> PL, C transportiert als Abnehmer, A zahlt EUSt",
        "companies": [
            {
                "id": 0,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": True,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "AT",
                "ship": True,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.BUYER,
            },
            {
                "id": 3,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # A -> B: Ruhend, Ort CN, Nicht EU-Steuerbar
            {
                "from": 0,
                "to": 1,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,
            },
            # B -> C: Bewegt, Ort DE, Steuerfrei IG (DE->AT)
            {
                "from": 1,
                "to": 2,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # C -> D: Ruhend, Ort PL, RC (AT->PL in PL)
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "PL",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (EUSt)
            1: {"DE"},  # B: DE (home, IG Lief B->C)
            2: {"AT", "PL"},  # C: AT (home, IG Erw), PL (RC Lief C->D)
            3: {"PL"},  # D: PL (home, IG Erw)
        },
    },
]
TEST_SCENARIOS_TEN_COMPANIES = [
    # --- Szenario 1: Rein EU, A transportiert ---
    # DE -> AT -> PL -> FR -> IT -> ES -> BE -> NL -> LU -> IE
    {
        "description": "10 Firmen (EU): DE -> ... -> IE, A transportiert",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": True,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 4,
                "country_code": "IT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 5,
                "country_code": "ES",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 6,
                "country_code": "BE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 7,
                "country_code": "NL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 8,
                "country_code": "LU",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 9,
                "country_code": "IE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # 0->1: Bewegt, Ort DE, Steuerfrei IG (DE->AT)
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_IC_SUPPLY,
            },
            # 1->2: Ruhend, Ort IE, RC (AT->PL in IE)
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "IE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 2->3: Ruhend, Ort IE, RC (PL->FR in IE)
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "IE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 3->4: Ruhend, Ort IE, RC (FR->IT in IE)
            {
                "from": 3,
                "to": 4,
                "moved": False,
                "place": "IE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 4->5: Ruhend, Ort IE, RC (IT->ES in IE)
            {
                "from": 4,
                "to": 5,
                "moved": False,
                "place": "IE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 5->6: Ruhend, Ort IE, RC (ES->BE in IE)
            {
                "from": 5,
                "to": 6,
                "moved": False,
                "place": "IE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 6->7: Ruhend, Ort IE, RC (BE->NL in IE)
            {
                "from": 6,
                "to": 7,
                "moved": False,
                "place": "IE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 7->8: Ruhend, Ort IE, RC (NL->LU in IE)
            {
                "from": 7,
                "to": 8,
                "moved": False,
                "place": "IE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 8->9: Ruhend, Ort IE, RC (LU->IE in IE) - Letzte Lieferung an IE in IE ist RC, da LU nicht in IE ansässig
            {
                "from": 8,
                "to": 9,
                "moved": False,
                "place": "IE",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (IG Lief)
            1: {"AT", "IE"},  # B: AT (home, IG Erw), IE (RC Lief)
            2: {"PL", "IE"},  # C: PL (home, IG Erw), IE (RC Lief)
            3: {"FR", "IE"},  # D: FR (home, IG Erw), IE (RC Lief)
            4: {"IT", "IE"},  # E: IT (home, IG Erw), IE (RC Lief)
            5: {"ES", "IE"},  # F: ES (home, IG Erw), IE (RC Lief)
            6: {"BE", "IE"},  # G: BE (home, IG Erw), IE (RC Lief)
            7: {"NL", "IE"},  # H: NL (home, IG Erw), IE (RC Lief)
            8: {"LU"},  # I: LU (home, IG Erw), IE (RC Lief)
            9: {"IE"},  # J: IE (home, IG Erw)
        },
    },
    # --- Szenario 2: Gemischt EU/Drittland, Mittlerer transportiert als Abnehmer, Export ---
    # DE -> AT -> CH -> PL -> FR -> US -> IT -> ES -> BE -> CN
    {
        "description": "10 Firmen (Gemischt): DE -> ... -> CN, F(US) transportiert als Abnehmer & Export",
        "companies": [
            {
                "id": 0,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 1,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "CH",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 4,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 5,
                "country_code": "US",
                "ship": True,
                "customs": True,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": IntermediaryStatus.BUYER,
            },  # F transportiert als Abnehmer & macht Export
            {
                "id": 6,
                "country_code": "IT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 7,
                "country_code": "ES",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 8,
                "country_code": "BE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 9,
                "country_code": "CN",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # 0->1: Ruhend, Ort DE, Steuerpflichtig DE
            {
                "from": 0,
                "to": 1,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 1->2: Ruhend, Ort DE, Steuerpflichtig DE
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 2->3: Ruhend, Ort DE, Steuerpflichtig DE
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 3->4: Ruhend, Ort DE, Steuerpflichtig DE
            {
                "from": 3,
                "to": 4,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 4->5: Ruhend, Ort DE, Steuerpflichtig DE
            {
                "from": 4,
                "to": 5,
                "moved": False,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 5->6: Bewegt, Ort DE, Steuerfrei Export (DE->US)
            {
                "from": 5,
                "to": 6,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.EXEMPT_EXPORT,
            },
            # 6->7: Ruhend, Ort CN, Nicht EU-Steuerbar
            {
                "from": 6,
                "to": 7,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,
            },
            # 7->8: Ruhend, Ort CN, Nicht EU-Steuerbar
            {
                "from": 7,
                "to": 8,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,
            },
            # 8->9: Ruhend, Ort CN, Nicht EU-Steuerbar
            {
                "from": 8,
                "to": 9,
                "moved": False,
                "place": "CN",
                "vat": VatTreatmentType.OUT_OF_SCOPE,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: DE (Lief)
            1: {"AT", "DE"},  # B: AT (home), DE (Lief)
            2: {"DE"},  # C: CH (none EU), DE (Lief)
            3: {"PL", "DE"},  # D: PL (home), DE (Lief)
            4: {"FR", "DE"},  # E: FR (home), DE (Lief)
            5: {"DE"},  # F: US (none EU), DE (Export)
            6: {"IT"},  # G: IT (home)
            7: {"ES"},  # H: ES (home)
            8: {"BE"},  # I: BE (home)
            9: set(),  # J: CN (none EU)
        },
    },
    # --- Szenario 3: Gemischt EU/Drittland, A transportiert, Import mit §3(8) ---
    # CN -> DE -> AT -> PL -> FR -> IT -> ES -> BE -> NL -> LU
    {
        "description": "10 Firmen (Gemischt): CN -> ... -> LU, A(CN) transportiert & EUSt (§3(8))",
        "companies": [
            {
                "id": 0,
                "country_code": "CN",
                "ship": True,
                "customs": False,
                "import_vat": True,
                "vat_change_code": None,
                "intermediary_status": None,
            },  # A transportiert & zahlt EUSt
            {
                "id": 1,
                "country_code": "DE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 2,
                "country_code": "AT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 3,
                "country_code": "PL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 4,
                "country_code": "FR",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 5,
                "country_code": "IT",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 6,
                "country_code": "ES",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 7,
                "country_code": "BE",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 8,
                "country_code": "NL",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
            {
                "id": 9,
                "country_code": "LU",
                "ship": False,
                "customs": False,
                "import_vat": False,
                "vat_change_code": None,
                "intermediary_status": None,
            },
        ],
        "expected_deliveries": [
            # 0->1: Bewegt, Ort DE (verlagert!), Steuerpflichtig DE (Normal, da A EUSt zahlt)
            {
                "from": 0,
                "to": 1,
                "moved": True,
                "place": "DE",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
            # 1->2: Ruhend, Ort LU, RC (DE->AT in LU)
            {
                "from": 1,
                "to": 2,
                "moved": False,
                "place": "LU",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
            # 2->3: Ruhend, Ort LU, RC (AT->PL in LU)
            {
                "from": 2,
                "to": 3,
                "moved": False,
                "place": "LU",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
            # 3->4: Ruhend, Ort LU, RC (PL->FR in LU)
            {
                "from": 3,
                "to": 4,
                "moved": False,
                "place": "LU",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
            # 4->5: Ruhend, Ort LU, RC (FR->IT in LU)
            {
                "from": 4,
                "to": 5,
                "moved": False,
                "place": "LU",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
            # 5->6: Ruhend, Ort LU, RC (IT->ES in LU)
            {
                "from": 5,
                "to": 6,
                "moved": False,
                "place": "LU",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
            # 6->7: Ruhend, Ort LU, RC (ES->BE in LU)
            {
                "from": 6,
                "to": 7,
                "moved": False,
                "place": "LU",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
            # 7->8: Ruhend, Ort LU, RC (BE->NL in LU)
            {
                "from": 7,
                "to": 8,
                "moved": False,
                "place": "LU",
                "vat": VatTreatmentType.TAXABLE_REVERSE_CHARGE,
            },
            # 8->9: Ruhend, Ort LU, Steuerpflichtig LU (NL->LU in LU)
            {
                "from": 8,
                "to": 9,
                "moved": False,
                "place": "LU",
                "vat": VatTreatmentType.TAXABLE_NORMAL,
            },
        ],
        "expected_triangle": False,
        "expected_registrations": {
            0: {"DE"},  # A: CN (none EU), DE (EUSt, Lief)
            1: {"DE", "LU"},  # B: DE (home), LU (RC Lief)
            2: {"AT", "LU"},  # C: AT (home, IG Erw), LU (RC Lief)
            3: {"PL", "LU"},  # D: PL (home, IG Erw), LU (RC Lief)
            4: {"FR", "LU"},  # E: FR (home, IG Erw), LU (RC Lief)
            5: {"IT", "LU"},  # F: IT (home, IG Erw), LU (RC Lief)
            6: {"ES", "LU"},  # G: ES (home, IG Erw), LU (RC Lief)
            7: {"BE", "LU"},  # H: BE (home, IG Erw), LU (RC Lief)
            8: {"NL", "LU"},  # I: NL (home, IG Erw), LU (Lief)
            9: {"LU"},  # J: LU (home, IG Erw)
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
        company.responsible_for_import_vat = config.get("import_vat", False)

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
    "scenario",
    TEST_SCENARIOS_THREE_COMPANIES,
    ids=[s["description"] for s in TEST_SCENARIOS_THREE_COMPANIES],
)
def test_chain_transaction_scenarios_three_companies(scenario):
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


@pytest.mark.parametrize(
    "scenario",
    TEST_SCENARIOS_FOUR_COMPANIES,
    ids=[s["description"] for s in TEST_SCENARIOS_FOUR_COMPANIES],
)
def test_chain_transaction_scenarios_four_companies(scenario):
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


@pytest.mark.parametrize(
    "scenario",
    TEST_SCENARIOS_TEN_COMPANIES,
    ids=[s["description"] for s in TEST_SCENARIOS_TEN_COMPANIES],
)
def test_chain_transaction_scenarios_TEN_companies(scenario):
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


def test_error_on_single_company():
    """
    Testet, ob ein ValueError ausgelöst wird, wenn nur eine Firma vorhanden ist.
    """
    # 1. Testdaten vorbereiten (nur eine Firma)
    company_configs = [
        {
            "id": 0,
            "country_code": "DE",
            "ship": True,
            "customs": False,
            "import_vat": False,
            "vat_change_code": None,
            "intermediary_status": None,
        }
    ]
    companies = create_company_chain(company_configs)
    if not companies:
        pytest.fail("Fehler beim Erstellen der Firmenkette für Einzelfirma-Test")
    start_company = companies[0]
    # Ende ist dasselbe wie Start bei nur einer Firma
    end_company = companies[0]
    transaction = Transaktion(start_company, end_company)

    # 2. Prüfen, ob ValueError bei der Berechnung ausgelöst wird
    with pytest.raises(ValueError) as excinfo:
        transaction.calculate_delivery_and_vat()

    # 3. (Optional) Prüfen der Fehlermeldung
    assert "Mindestens zwei Firmen erforderlich" in str(
        excinfo.value
    ) or "Transaktion benötigt mindestens 2 Firmen" in str(excinfo.value)
    print("\n--- Test Passed: Fehler bei Einzelfirma korrekt ausgelöst ---")
