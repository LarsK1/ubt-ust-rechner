from random import randrange

import streamlit as st
from graphviz import Digraph

from helpers.countries import Country
from helpers.fixed_header import st_fixed_container
from helpers.helpers import (
    get_countries,
    Handelsstufe,
    Transaktion,
    Lieferung,
    IntermediaryStatus,
)


def helper_switch_page(page, options):
    """
    Helper function to switch between pages.
    """
    st.session_state["aktuelle_seite"] = page
    if page == 1:
        st.session_state["transaction"] = Transaktion(options[0], options[-1])


def Eingabe_1():
    st.title("USt-Reihengeschäfte - Dateneingabe")
    laender_firmen: list[Handelsstufe] = []
    show_next_steps = False

    # Liste der verfügbaren Länder auf Deutsch
    laender = get_countries()
    schritt = 0

    diagram = st_fixed_container(mode="sticky", position="top", margin="0px")

    with st.expander(
        "Grundlegende Daten", expanded=True
    ):  # Standardmäßig geöffnet für bessere UX
        st.subheader("Schritt 1: Anzahl der beteiligten Firmen")
        # Anzahl der beteiligten Firmen festlegen
        anzahl_firmen = st.number_input(
            "Anzahl der beteiligten Firmen:",
            min_value=2,
            step=1,
            value=3,  # Min_value auf 2 gesetzt
        )
        # --- Session State Management für Anzahl und Länder ---
        if (
            "anzahl_firmen_saved" not in st.session_state
            or anzahl_firmen != st.session_state.get("anzahl_firmen_saved")
        ):
            st.session_state["anzahl_firmen_saved"] = anzahl_firmen
            st.session_state["firmenland_indices"] = [
                randrange(0, len(laender)) for _ in range(anzahl_firmen)
            ]
            # Reset other relevant states if number changes
            st.session_state.pop("abweichende_ust_ids", None)
            st.session_state.pop("transport_firma_index", None)
            st.session_state.pop("intermediary_status", None)
            st.session_state.pop("customs_export_index", None)
            st.session_state.pop("customs_import_vat_index", None)

        # --- Länderauswahl (Schritt 2) ---
        if anzahl_firmen >= 2:  # Mindestens 2 Firmen für ein Geschäft
            st.divider()
            st.subheader("Schritt 2: Firmensitz")
            selected_countries = []
            for i in range(anzahl_firmen):
                role = (
                    "Verkäufer"
                    if i == 0
                    else (
                        "Empfänger"
                        if i == anzahl_firmen - 1
                        else f"Zwischenhändler {i}"
                    )
                )
                # Verwende gespeicherte Indizes für Konsistenz
                selected_country = st.selectbox(
                    f"{role}:",
                    laender,
                    key=f"firma_{i}",
                    index=st.session_state["firmenland_indices"][i],
                    format_func=lambda c: f"{c.name} ({c.code}){' - EU' if c.EU else ''}",  # Bessere Anzeige
                )
                selected_countries.append(selected_country)
                # Update session state index if changed by user
                st.session_state["firmenland_indices"][i] = laender.index(
                    selected_country
                )

            # Erstelle Handelsstufen-Objekte
            laender_firmen = [
                Handelsstufe(country, i, anzahl_firmen)
                for i, country in enumerate(selected_countries)
            ]

            # Verknüpfe die Kette
            for i, firma in enumerate(laender_firmen):
                if i > 0:
                    firma.add_previous_company_to_chain(firma, laender_firmen[i - 1])
                if i < anzahl_firmen - 1:
                    firma.add_next_company_to_chain(firma, laender_firmen[i + 1])

            export_relevant = False
            import_relevant = False
            if len(laender_firmen) >= 2:  # Nur prüfen, wenn mind. 2 Firmen da sind
                for i in range(len(laender_firmen) - 1):
                    lieferant_firma = laender_firmen[i]
                    kunde_firma = laender_firmen[i + 1]

                    # Prüfe auf Export (EU -> Nicht-EU)
                    if lieferant_firma.country.EU and not kunde_firma.country.EU:
                        export_relevant = True
                        # Optional: Hier könnte man auch prüfen, ob der Transport über diese Grenze geht,
                        # aber für die reine Anzeige des Zoll-Abschnitts reicht die Länderkombi.

                    # Prüfe auf Import (Nicht-EU -> EU)
                    if not lieferant_firma.country.EU and kunde_firma.country.EU:
                        import_relevant = True

                    # Wenn beides gefunden, kann die Schleife abbrechen (optional)
                    if export_relevant and import_relevant:
                        break

            # --- NEU: Prüfung auf mindestens ein EU-Land ---
            at_least_one_eu = any(f.country.EU for f in laender_firmen)
            if not at_least_one_eu and anzahl_firmen > 0:
                st.warning(
                    "Bitte wählen Sie mindestens eine Firma mit Sitz in der EU aus, um umsatzsteuerliche EU-Regeln anwenden zu können.",
                    icon="🇪🇺",
                )
                show_next_steps = False
            elif anzahl_firmen < 3:
                st.warning(
                    "Ein Reihengeschäft im umsatzsteuerlichen Sinne erfordert mindestens drei beteiligte Firmen.",
                    icon="⚠️",
                )
                show_next_steps = False  # Reihengeschäft-spezifische Logik erst ab 3
            else:
                show_next_steps = True  # Voraussetzung für nächste Schritte erfüllt

            # --- Besondere Merkmale (Schritt 3) ---
            if show_next_steps:  # Nur anzeigen, wenn mind. 1 EU-Land und >= 3 Firmen
                st.divider()
                st.subheader("Schritt 3: Besondere Merkmale der EU-Firmen")
                # Initialisiere Session State für Checkboxen, falls nicht vorhanden
                if "abweichende_ust_ids" not in st.session_state:
                    st.session_state["abweichende_ust_ids"] = {}

                for i, firma in enumerate(laender_firmen):
                    if not firma.country.EU:
                        continue  # Nur für EU-Firmen relevant

                    container_land = st.container(border=True)
                    col1, col2 = container_land.columns((1, 8))
                    if firma.country.flag:
                        col1.image(firma.country.flag, width=60)  # Etwas kleiner

                    role_name = firma.get_role_name(True)
                    col2.write(f"**{role_name}: {firma.country.name} - EU**")

                    # Verwende Session State für Checkbox-Status
                    ust_key = f"abweichende_ust_id_{i}"
                    ust_checked = col2.checkbox(
                        "Vom Heimatland abweichende USt-ID verwenden?",
                        key=ust_key,
                        value=st.session_state["abweichende_ust_ids"].get(
                            ust_key, False
                        ),
                    )
                    st.session_state["abweichende_ust_ids"][
                        ust_key
                    ] = ust_checked  # Status speichern

                    if ust_checked:
                        laender_ohne_eigenes = [
                            l for l in laender if l.code != firma.country.code and l.EU
                        ]
                        if laender_ohne_eigenes:  # Nur anzeigen, wenn Auswahl möglich
                            target_country_vat_id = col2.selectbox(
                                f"Land der verwendeten USt-ID:",
                                laender_ohne_eigenes,
                                key=f"land_abweichende_ust_id_{i}",
                                format_func=lambda c: f"{c.name} ({c.code})",  # Bessere Anzeige
                            )
                            firma.set_changed_vat_id(target_country_vat_id)
                        else:
                            col2.warning(
                                "Keine anderen EU-Länder zur Auswahl verfügbar."
                            )
                            # Reset state if checkbox is unchecked or no options
                            firma.set_changed_vat_id(None)
                    else:
                        # Reset state if checkbox is unchecked
                        firma.set_changed_vat_id(None)

                schritt = 1  # Schritt 1 (Daten) abgeschlossen, wenn wir hier sind
            else:
                schritt = 0  # Bedingungen für nächste Schritte nicht erfüllt
        else:
            # Weniger als 2 Firmen
            st.error("Ein Handelsgeschäft benötigt mindestens zwei beteiligte Firmen.")
            schritt = 0

    # --- Lieferung / Zollabwicklung (Schritte 4, 5, 5b) ---
    if schritt == 1 and show_next_steps:
        endanalyse_benötigte_daten = False
        with st.expander("Lieferung / Zollabwicklung", expanded=True):
            st.subheader("Schritt 4: Lieferung")

            transport_options = ["keine Auswahl"] + laender_firmen
            default_transport_index = st.session_state.get("transport_firma_index", 0)
            selected_transport_index = st.selectbox(
                "Welche Firma transportiert die Ware / veranlasst den Transport?",
                range(len(transport_options)),
                index=default_transport_index,
                format_func=lambda idx: str(transport_options[idx]),
                key="transport_select",
            )
            st.session_state["transport_firma_index"] = selected_transport_index
            transport_firma = transport_options[selected_transport_index]

            is_transport_selected = False
            if isinstance(transport_firma, Handelsstufe):
                is_transport_selected = True
                for firma in laender_firmen:
                    firma.responsible_for_shippment = (
                        firma.identifier == transport_firma.identifier
                    )
                st.success(f"Transport durch: **{transport_firma}**", icon="🚚")
            else:
                for firma in laender_firmen:
                    firma.responsible_for_shippment = False

            is_intermediary_status_set = False
            is_intermediary_relevant = (
                is_transport_selected and "Z" in transport_firma.get_role_name()
            )

            if is_intermediary_relevant:
                st.info(
                    f"Da der {transport_firma.get_role_name(True)} transportiert, ist sein Status relevant.",
                    icon="ℹ️",
                )
                intermediary_options = ["keine Auswahl", "Abnehmer", "Lieferer"]
                default_intermediary_index = st.session_state.get(
                    "intermediary_status_index", 0
                )
                selected_intermediary_index = st.selectbox(
                    "Status des transportierenden Zwischenhändlers:",
                    range(len(intermediary_options)),
                    index=default_intermediary_index,
                    format_func=lambda idx: intermediary_options[idx],
                    key="intermediary_select",
                )
                st.session_state["intermediary_status_index"] = (
                    selected_intermediary_index
                )
                intermediar_status_str = intermediary_options[
                    selected_intermediary_index
                ]

                status_to_set = None
                if intermediar_status_str == "Abnehmer":
                    status_to_set = IntermediaryStatus.BUYER
                    is_intermediary_status_set = True
                elif intermediar_status_str == "Lieferer":
                    status_to_set = (
                        IntermediaryStatus.SUPPLIER
                    )  # Oder OCCURING_SUPPLIER
                    is_intermediary_status_set = True
                # Wenn "keine Auswahl", bleibt is_intermediary_status_set = False

                for firma in laender_firmen:
                    if firma.identifier == transport_firma.identifier:
                        firma.intermediary_status = status_to_set
                        break
            else:
                # Wenn kein ZH transportiert, ist der Status nicht relevant -> Bedingung erfüllt
                is_intermediary_status_set = True
                # Status für alle resetten (falls vorher mal einer gesetzt war)
                for firma in laender_firmen:
                    firma.intermediary_status = None

            # --- Zollabwicklung (Schritt 5 & 5b) ---
            # Standardmäßig True, wenn nicht relevant, sonst False bis Auswahl
            is_customs_export_set = not export_relevant
            is_customs_import_vat_set = not import_relevant

            # --- Schritt 5: Export-Zoll ---
            if export_relevant:
                st.divider()
                st.subheader("Schritt 5: Zollabwicklung (Export)")
                st.info(
                    "Da die Lieferung von der EU in ein Drittland geht, ist die Export-Zollabwicklung relevant.",
                    icon="🛂",
                )
                customs_export_options = ["keine Auswahl"] + laender_firmen
                default_export_index = st.session_state.get("customs_export_index", 0)
                selected_export_index = st.selectbox(
                    "Wer übernimmt die Zollabwicklung beim Export?",
                    range(len(customs_export_options)),
                    index=default_export_index,
                    format_func=lambda idx: str(customs_export_options[idx]),
                    key="customs_export_select",
                )
                st.session_state["customs_export_index"] = selected_export_index
                customs_export_firma = customs_export_options[selected_export_index]

                if isinstance(customs_export_firma, Handelsstufe):
                    is_customs_export_set = True  # Jetzt auf True setzen
                    for firma in laender_firmen:
                        firma.responsible_for_customs = (
                            firma.identifier == customs_export_firma.identifier
                        )
                    st.success(
                        f"Export-Zoll durch: **{customs_export_firma}**", icon="👍"
                    )  # Icon geändert
                else:
                    # is_customs_export_set bleibt False
                    for firma in laender_firmen:
                        firma.responsible_for_customs = False

            # --- Schritt 5b: Einfuhrumsatzsteuer ---
            if import_relevant:
                st.divider()
                st.subheader("Schritt 5b: Einfuhrumsatzsteuer (EUSt)")
                st.info(
                    "Da die Lieferung aus einem Drittland in die EU geht, ist die Einfuhrumsatzsteuer relevant.",
                    icon="🇪🇺",
                )
                customs_import_vat_options = ["keine Auswahl"] + laender_firmen
                default_import_vat_index = st.session_state.get(
                    "customs_import_vat_index", 0
                )
                selected_import_vat_index = st.selectbox(
                    "Wer meldet die Einfuhr an und schuldet die Einfuhrumsatzsteuer?",
                    range(len(customs_import_vat_options)),
                    index=default_import_vat_index,
                    format_func=lambda idx: str(customs_import_vat_options[idx]),
                    key="customs_import_vat_select",
                )
                st.session_state["customs_import_vat_index"] = selected_import_vat_index
                customs_import_vat_firma = customs_import_vat_options[
                    selected_import_vat_index
                ]

                if isinstance(customs_import_vat_firma, Handelsstufe):
                    is_customs_import_vat_set = True  # Jetzt auf True setzen
                    for firma in laender_firmen:
                        if not hasattr(firma, "responsible_for_import_vat"):
                            firma.responsible_for_import_vat = False
                        firma.responsible_for_import_vat = (
                            firma.identifier == customs_import_vat_firma.identifier
                        )
                    st.success(
                        f"EUSt-Anmeldung durch: **{customs_import_vat_firma}**",
                        icon="💶",
                    )
                else:
                    # is_customs_import_vat_set bleibt False
                    for firma in laender_firmen:
                        if hasattr(firma, "responsible_for_import_vat"):
                            firma.responsible_for_import_vat = False

            # --- Analyse-Button (Schritt 6) ---
            # Alle notwendigen Bedingungen prüfen
            endanalyse_benötigte_daten = (
                is_transport_selected
                and is_intermediary_status_set
                and is_customs_export_set  # Ist True wenn nicht relevant, oder wenn Auswahl getroffen
                and is_customs_import_vat_set  # Ist True wenn nicht relevant, oder wenn Auswahl getroffen
            )

            if endanalyse_benötigte_daten:
                st.divider()
                st.subheader("Schritt 6: Analyse")
                st.success(
                    "Alle notwendigen Daten sind erfasst. Sie können die Analyse starten.",
                    icon="✅",
                )
                st.button(
                    "Analyse starten",
                    icon="🛫",
                    on_click=helper_switch_page,
                    args=(1, laender_firmen),
                    use_container_width=True,
                )
            else:
                missing_data = []
                if not is_transport_selected:
                    missing_data.append("Transporteur auswählen (Schritt 4)")
                if not is_intermediary_status_set:
                    missing_data.append(
                        "Status des transportierenden Zwischenhändlers auswählen (Schritt 4)"
                    )
                # Nur hinzufügen, wenn relevant UND nicht gesetzt
                if export_relevant and not is_customs_export_set:
                    missing_data.append("Export-Zollabwickler auswählen (Schritt 5)")
                if import_relevant and not is_customs_import_vat_set:
                    missing_data.append(
                        "Verantwortlichen für EUSt auswählen (Schritt 5b)"
                    )

                if missing_data:
                    st.divider()
                    st.subheader("Schritt 6: Analyse")
                    st.warning(
                        f"Bitte vervollständigen Sie die Eingaben: {', '.join(missing_data)}.",
                        icon="❗",
                    )

    # --- Diagramm (immer anzeigen, wenn Kette existiert) ---
    if len(laender_firmen) >= 2:  # Mindestens 2 Firmen für Diagramm
        transaction = Transaktion(laender_firmen[0], laender_firmen[-1])
        dot = Digraph(comment="Geschäftsablauf", graph_attr={"rankdir": "LR"})
        with dot.subgraph() as s:
            s.attr("node", shape="box")
            for company in transaction.get_ordered_chain_companies():
                company_text = f"{company.get_role_name(True)}"
                # Zusatzinfos: Abw. USt-ID und Status
                zusatz_infos = []
                if company.changed_vat and company.new_country:
                    zusatz_infos.append(f"USt-ID: {company.new_country.code}\n")
                if company.intermediary_status is not None:
                    zusatz_infos.append(
                        f"Status: {company.get_intermideary_status()}\n"
                    )
                if company.responsible_for_import_vat:
                    zusatz_infos.append("EUSt-Anmeldung\n")

                if zusatz_infos:
                    company_text += "\n" + "".join(zusatz_infos)
                else:
                    company_text += "\n--------\n "  # Minimaler Platzhalter für Höhe
                company_text += f"{company.country.name} ({company.country.code})"
                if company.country.EU:
                    company_text += ", EU"
                else:
                    # Kleinerer Platzhalter oder ganz weglassen
                    company_text += "\n"  # Minimaler Abstand

                # Farbliche Markierung (Transporteur/Zoll/EUSt)
                colors = []
                if company.responsible_for_shippment:
                    colors.append("#ffa500")  # Orange für Transport
                if company.responsible_for_customs:
                    colors.append("#b2d800")  # Grün für Export-Zoll
                if company.responsible_for_import_vat:
                    colors.append("#add8e6")  # Hellblau für EUSt

                node_attrs = {}
                if colors:
                    node_attrs["style"] = "filled"
                    if len(colors) > 1:
                        node_attrs["fillcolor"] = ":".join(colors)  # Gradient
                    else:
                        node_attrs["fillcolor"] = colors[0]

                s.node(str(company.identifier), company_text, **node_attrs)

        # Kanten für Rechnung/Bestellung/Transport
        for company in laender_firmen:
            if company.next_company:
                dot.edge(
                    str(company.identifier),
                    str(company.next_company.identifier),
                    "Rechnung",
                    color="orange",
                )
                dot.edge(
                    str(company.next_company.identifier),
                    str(company.identifier),
                    "Bestellung",
                    style="dashed",
                    color="grey",
                )
        if transaction.find_shipping_company():
            dot.edge(
                str(transaction.start_company.identifier),
                str(transaction.end_company.identifier),
                f"Transport durch {transaction.shipping_company.get_role_name(True)} - {transaction.shipping_company.country.name} ({transaction.shipping_company.country.code})",
                style="bold",
                color="blue",
                splines="polyline",
            )

        diagram.graphviz_chart(dot, use_container_width=True)


def Analyse_1():
    if "transaction" in st.session_state:
        transaction: Transaktion = st.session_state["transaction"]

        st.title("USt-Reihengeschäfte - Analyse")
        try:
            # Berechnung durchführen (nur einmal)
            alle_lieferungen: list[Lieferung] = transaction.calculate_delivery_and_vat()
            is_triangle = transaction.is_triangular_transaction()
            if is_triangle:
                st.success(
                    """**Dreiecksgeschäft erkannt!**
					Die Voraussetzungen für die Vereinfachungsregelung nach § 25b UStG / Art. 141 MwStSystRL scheinen erfüllt zu sein.
					Beachten Sie die besonderen Rechnungslegungs- und Meldepflichten.
					""",
                    icon="🔺",
                )
            dot_analyse = Digraph(
                comment="Analyse Reihengeschäft", graph_attr={"rankdir": "LR"}
            )

            # 1. Knoten (Firmen) erstellen
            with dot_analyse.subgraph() as s:
                s.attr("node", shape="box")
                firmen_im_graph = transaction.get_ordered_chain_companies()
                for company in firmen_im_graph:
                    # Basis-Label wie in der Eingabe
                    company_text = f"{company.get_role_name(True)}\n{company.country.name} ({company.country.code})"
                    if company.country.EU:
                        company_text += ", EU"

                    if company.changed_vat and company.new_country:
                        company_text += f"\nabw. USt-ID: {company.new_country.code}"
                    s.node(str(company.identifier), company_text)

            # 2. Kanten (Rechnungen UND ruhende Lieferungen) erstellen
            bewegte_lieferung_gefunden: Lieferung | None = None
            for lief in alle_lieferungen:
                # --- Rechnungskante
                rechnungs_label = f"{lief.get_vat_treatment_display()}"
                if (
                    lief.invoice_note
                    and "Steuerfrei" not in lief.invoice_note
                    and "Reverse Charge" not in lief.invoice_note
                    and "Nicht steuerbar" not in lief.invoice_note
                ):
                    rechnungs_label += f"\n({lief.invoice_note})"

                dot_analyse.edge(
                    str(lief.lieferant.identifier),
                    str(lief.kunde.identifier),
                    label=rechnungs_label,
                    color="orange",  # Farbe für Rechnungen
                    fontsize="10",
                )

                # --- Kante für Ruhende Lieferung ---
                if not lief.is_moved_supply:
                    ruhend_label = f"ruhende Lieferung\n"
                    dot_analyse.edge(
                        str(lief.lieferant.identifier),
                        str(lief.kunde.identifier),
                        label=ruhend_label,
                        color="grey",  # Andere Farbe für ruhende Lieferung
                        style="dashed",  # Gestrichelt zur Unterscheidung
                        fontsize="9",  # Etwas kleiner
                    )
                else:
                    # Merke dir die bewegte Lieferung für die separaten Kanten
                    bewegte_lieferung_gefunden = lief

            # 3. Kante für die RECHTLICH bewegte Lieferung (BLAU)
            if bewegte_lieferung_gefunden:
                bewegte_label = f"bewegte Lieferung"
                dot_analyse.edge(
                    # Von Lieferant zu Kunde DIESER Lieferung
                    str(bewegte_lieferung_gefunden.lieferant.identifier),
                    str(bewegte_lieferung_gefunden.kunde.identifier),
                    label=bewegte_label,
                    color="blue",  # Farbe für rechtlich bewegte Lieferung
                    style="bold",
                    fontsize="10",
                    # constraint='false' # Kann helfen, Layout zu entzerren
                )

            # 4. Kante für den PHYSISCHEN Transportweg (GRÜN)
            if transaction.shipping_company:  # Nur wenn ein Transporteur bekannt ist
                transport_label = f"physischer Transport\ndurch {transaction.shipping_company.get_role_name(True)}"
                dot_analyse.edge(
                    # Von erster zu letzter Firma
                    str(transaction.start_company.identifier),
                    str(transaction.end_company.identifier),
                    label=transport_label,
                    color="green",  # Farbe für physischen Transport
                    style="bold, dotted",  # Fett und gepunktet zur Unterscheidung
                    fontsize="10",
                    splines="polyline",  # Oder polyline, um Knoten zu umgehen
                    # constraint='false' # Kann helfen, Layout zu entzerren
                )

            # Graph anzeigen
            st.graphviz_chart(dot_analyse, use_container_width=True)
            # --- Abschnitt Lieferungen ---
            with st.expander("Übersicht der Lieferungen", icon="🚚", expanded=True):
                # 1. Bewegte Lieferung anzeigen
                st.markdown("#### Bewegte Lieferung")
                bewegte_lieferung = next(
                    (l for l in alle_lieferungen if l.is_moved_supply), None
                )
                if bewegte_lieferung:
                    st.markdown(
                        f"- {bewegte_lieferung.lieferant} -> {bewegte_lieferung.kunde}, Ort: {bewegte_lieferung.place_of_supply}, USt: {bewegte_lieferung.get_vat_treatment_display()}"
                    )
                else:
                    st.warning("Keine bewegte Lieferung gefunden.", icon="⚠️")

                # 2. Ruhende Lieferungen anzeigen
                st.markdown("#### Ruhende Lieferungen")
                ruhende_lieferungen = [
                    l for l in alle_lieferungen if not l.is_moved_supply
                ]
                if ruhende_lieferungen:
                    for lief in ruhende_lieferungen:
                        st.markdown(
                            f"- {lief.lieferant} -> {lief.kunde}, Ort: {lief.place_of_supply}, USt: {lief.get_vat_treatment_display()}"
                        )
                else:
                    st.info("Keine ruhenden Lieferungen vorhanden.")

            # --- Abschnitt Rechnungsstellung ---
            # Nur anzeigen, wenn die Berechnung erfolgreich war
            if alle_lieferungen:
                with st.expander("Übersicht der Rechnungsstellung", icon="📝"):
                    st.markdown("#### Rechnungsdetails pro Lieferung")
                    lief: Lieferung  # Type Hint für Klarheit
                    for i, lief in enumerate(alle_lieferungen):
                        st.markdown(f"**Rechnung {i+1}:**")
                        col1, col2 = st.columns([1, 4])  # Verhältnis anpassbar
                        with col1:
                            st.markdown(f"**Lieferant:**")
                            st.markdown(f"**Kunde:**")
                            st.markdown(f"**Behandlung:**")
                        with col2:
                            # Verwende die __repr__ der Handelsstufe für Lieferant/Kunde
                            st.markdown(f"{lief.lieferant}")
                            st.markdown(f"{lief.kunde}")
                            # Verwende die benutzerfreundliche Anzeige der Behandlung
                            st.markdown(f"*{lief.get_vat_treatment_display()}*")
                            if lief.invoice_note:
                                st.caption(f"Hinweis: {lief.invoice_note}")
                        if i < len(alle_lieferungen) - 1:
                            st.divider()  # Trennlinie nach jeder Rechnung
            if alle_lieferungen:
                try:  # Nur anzeigen, wenn Berechnung erfolgreich war
                    registration_data = transaction.determine_registration_obligations()
                    with st.expander(
                        "Mögliche Registrierungspflichten (EU)",
                        icon="🇪🇺",
                        expanded=False,
                    ):
                        st.markdown("#### Notwendige USt-Registrierungen pro Firma")
                        st.caption(
                            "Dies ist eine automatisierte Einschätzung basierend auf den Lieferungen. Die tatsächliche Notwendigkeit kann von weiteren Faktoren abhängen."
                        )

                        firma: Handelsstufe
                        registrierungen: set[
                            Country
                        ]  # Das ist ein Set von Country Objekten

                        # Iteriere durch die Firmen in der Reihenfolge der Kette für bessere Lesbarkeit
                        firmen_in_order = transaction.get_ordered_chain_companies()
                        data_items = [
                            (f, registration_data.get(f, set()))
                            for f in firmen_in_order
                        ]  # Stelle sicher, dass alle Firmen berücksichtigt werden

                        for firma, registrierungen_set in data_items:
                            # Überspringe Firmen ohne EU-Registrierungsbedarf oder Drittlandsfirmen ohne Bedarf
                            # Diese Bedingung könnte zu streng sein, wenn eine Drittlandsfirma Registrierungen hat
                            # Besser: Prüfen, ob überhaupt Registrierungen vorhanden sind
                            # if not firma.country.EU and not registrierungen_set:
                            #    continue

                            st.markdown(
                                f"**{firma}**"  # Nutzt die __repr__ der Handelsstufe
                            )

                            if not registrierungen_set:
                                # Keine Registrierungen für diese Firma gefunden
                                st.markdown(
                                    "- *Keine EU-Registrierungspflicht aus dieser Transaktion ersichtlich.*"
                                )
                            else:
                                # Sortiere die Länder für eine konsistente Ausgabe
                                # Wichtig: Konvertiere das Set in eine Liste zum Sortieren!
                                sorted_registrations = sorted(
                                    list(registrierungen_set), key=lambda c: c.name
                                )

                                found_registration = False
                                for country in sorted_registrations:
                                    found_registration = True
                                    if country == firma.country:
                                        # Heimatland ist erforderlich
                                        st.markdown(
                                            f"- {country.name} ({country.code}) - *Heimatland*"
                                        )
                                    else:
                                        # Zusätzliche Registrierung erforderlich
                                        st.markdown(
                                            f"- :red[{country.name} ({country.code}) - *Zusätzlich erforderlich*]"
                                        )

                                # Fallback, falls das Set leer war (sollte durch obige Prüfung abgedeckt sein)
                                if not found_registration:
                                    st.markdown(
                                        "- *Keine EU-Registrierungspflicht aus dieser Transaktion ersichtlich.*"
                                    )

                            # Trennlinie nach jeder Firma, außer der letzten
                            # Finde den Index der aktuellen Firma in der geordneten Liste
                            current_index = firmen_in_order.index(firma)
                            if current_index < len(firmen_in_order) - 1:
                                st.divider()

                except KeyError as e:
                    st.error(
                        f"Fehler beim Zugriff auf Registrierungsdaten für Firma: {e}. Möglicherweise fehlt eine Firma im Ergebnis von determine_registration_obligations.",
                        icon="❌",
                    )
                except Exception as e:
                    st.error(
                        f"Fehler bei der Ermittlung der Registrierungspflichten: {e}",
                        icon="🔥",
                    )
            if alle_lieferungen:
                try:
                    reporting_data = transaction.determine_reporting_obligations()
                    # Prüfen, ob überhaupt Meldepflichten gefunden wurden
                    has_reporting_needs = any(reporting_data.values())

                    if has_reporting_needs:
                        with st.expander(
                            "Mögliche Meldepflichten (EU - ohne Schwellenwerte)",
                            icon="📊",
                            expanded=False,  # Standardmäßig geschlossen
                        ):
                            st.markdown("#### Potenzielle Meldungen pro Firma")
                            st.caption(
                                """
								**Wichtige Hinweise:**
								*   **Intrastat:** Meldepflichten (Versendung/Eingang) entstehen erst **ab Erreichen nationaler Schwellenwerte**. Diese variieren je EU-Land und Melderichtung.
								*   **Zusammenfassende Meldung (ZM):** Für steuerfreie innergemeinschaftliche Lieferungen erforderlich. Die **korrekte USt-Id des Abnehmers** und weitere **Nachweise** (z.B. Gelangensbestätigung) sind entscheidend für die Steuerfreiheit. Bei Dreiecksgeschäften gelten besondere Kennzeichnungspflichten.
								*   Die Anzeige hier stellt **keine** Berücksichtigung dieser Schwellenwerte oder detaillierten Nachweispflichten dar.
								"""
                            )

                            firmen_in_order = transaction.get_ordered_chain_companies()
                            data_items = [
                                (f, reporting_data.get(f, set()))
                                for f in firmen_in_order
                            ]

                            for firma, meldungen_set in data_items:
                                # Nur Firmen anzeigen, die Meldepflichten haben
                                if meldungen_set:
                                    st.markdown(f"**{firma}**")  # Nutzt __repr__

                                    sorted_meldungen = sorted(list(meldungen_set))
                                    for meldung in sorted_meldungen:
                                        st.markdown(f"- {meldung}")

                                    current_index = firmen_in_order.index(firma)
                                    if current_index < len(firmen_in_order) - 1:
                                        # Trennlinie nur, wenn noch eine Firma mit Meldungen folgt
                                        next_firma_has_needs = any(
                                            reporting_data.get(f, set())
                                            for f in firmen_in_order[
                                                current_index + 1 :
                                            ]
                                        )
                                        if next_firma_has_needs:
                                            st.divider()

                except Exception as e:
                    st.error(
                        f"Fehler bei Ermittlung der Meldepflichten: {e}", icon="🔥"
                    )
        except ValueError as e:
            st.error(f"Fehler bei der Berechnung der Lieferungen: {e}", icon="❌")
            # Setze alle_lieferungen auf None oder leere Liste, um Fehler im nächsten Abschnitt zu vermeiden
            alle_lieferungen = []
        except Exception as e:  # Fange auch andere mögliche Fehler ab
            st.error(f"Ein unerwarteter Fehler ist aufgetreten: {e}", icon="🔥")
            alle_lieferungen = []  # Sicherstellen, dass die Liste leer ist bei Fehlern

        # --- Zurück-Button ---
        st.button(
            "Zurück zur Eingabe", icon="⬅️", on_click=helper_switch_page, args=(0, None)
        )

    else:
        # Fallback, falls die Transaktion nicht im Session State ist
        st.warning(
            "Keine Transaktionsdaten gefunden. Bitte gehen Sie zurück zur Eingabe."
        )
        if st.button("Zurück zur Eingabe", icon="⬅️"):
            st.session_state["aktuelle_seite"] = 0
            st.rerun()


if "aktuelle_seite" not in st.session_state:
    st.session_state["aktuelle_seite"] = 0

if st.session_state["aktuelle_seite"] == 0:
    Eingabe_1()
elif st.session_state["aktuelle_seite"] == 1:
    Analyse_1()
else:
    st.session_state["aktuelle_seite"] = 0
    st.rerun()
