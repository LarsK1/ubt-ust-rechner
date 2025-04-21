from random import randrange

import streamlit as st
from graphviz import Digraph

from helpers.countries import Country
from helpers.fixed_header import st_fixed_container
from helpers.helpers import get_countries, Handelsstufe, Transaktion, Lieferung, IntermediaryStatus

st.title("USt-Reihengeschäfte")


def helper_switch_page(page, options):
    """
    Helper function to switch between pages.
    """
    st.session_state["aktuelle_seite"] = page
    if page == 1:
        st.session_state["transaction"] = Transaktion(options[0], options[-1])


def Eingabe_1():
    laender_firmen: list[Handelsstufe] = []

    # Liste der verfügbaren Länder auf Deutsch
    laender = get_countries()
    schritt = 0

    diagram = st_fixed_container(
        mode="sticky", position="top", border=True, margin="0px"
    )

    with st.expander("Grundlegende Daten"):
        st.subheader("Schritt 1: Anzahl der beteiligten Firmen")
        # Anzahl der beteiligten Firmen festlegen
        anzahl_firmen = st.number_input(
            "Anzahl der beteiligten Firmen:", min_value=1, step=1, value=3
        )
        if "anzahl_firmen_saved" not in st.session_state:
            st.session_state["anzahl_firmen_saved"] = anzahl_firmen
            st.session_state["firmenland"] = []
            for i in range(anzahl_firmen):
                st.session_state["firmenland"].append(randrange(0, len(laender)))
        else:
            if anzahl_firmen != st.session_state["anzahl_firmen_saved"]:
                st.session_state["firmenland"] = []
                for i in range(anzahl_firmen):
                    st.session_state["firmenland"].append(randrange(0, len(laender)))
                st.session_state["anzahl_firmen_saved"] = anzahl_firmen
        if anzahl_firmen > 2:
            st.divider()
            # Länderauswahl für jede Firma
            if anzahl_firmen:
                st.subheader("Schritt 2: Firmensitz")
                for i in range(int(anzahl_firmen)):
                    if i == 0:
                        land = st.selectbox(
                            f"Verkäufer:",
                            laender,
                            key=f"firma_{i}",
                            index=st.session_state["firmenland"][i],
                        )
                    elif i == anzahl_firmen - 1:
                        land = st.selectbox(
                            f"Empfänger:",
                            laender,
                            key=f"firma_{i}",
                            index=st.session_state["firmenland"][i],
                        )
                    else:
                        land = st.selectbox(
                            f"Zwischenhändler {i}:",
                            laender,
                            key=f"firma_{i}",
                            index=st.session_state["firmenland"][i],
                        )
                    laender_firmen.append(Handelsstufe(land, i, int(anzahl_firmen)))
                for i, land in enumerate(laender_firmen):
                    land: Handelsstufe
                    if i == 0:
                        land.add_next_company_to_chain(land, laender_firmen[i + 1])
                    elif i == int(anzahl_firmen) - 1:
                        land.add_previous_company_to_chain(land, laender_firmen[i - 1])
                    else:
                        land.add_previous_company_to_chain(land, laender_firmen[i - 1])
                        land.add_next_company_to_chain(land, laender_firmen[i + 1])
                st.divider()
                # Ausgabe der ausgewählten Länder
                if len(laender_firmen) > 0:
                    st.subheader("Schritt 3: Besondere Merkmale der EU-Firmen")
                    if not any(
                        laender_firmen[i].country.EU is True
                        for i in range(len(laender_firmen))
                    ):
                        st.warning(
                            "Alle Firmen sind außerhalb der EU ansässig. Eine Nuztung einer abweichenden USt-ID ist nur in Europa möglich."
                        )
                    else:
                        for i, land in enumerate(laender_firmen):
                            land: Handelsstufe
                            if not land.country.EU:
                                continue
                            container_land = st.container(border=True)
                            coulumn1, column2 = container_land.columns(
                                (
                                    1,
                                    8,
                                )
                            )
                            if land.country.flag:
                                coulumn1.image(land.country.flag, width=100)

                            if i == 0:
                                column2.write(
                                    f"**Verkäufer: {land.country.name} - {'EU' if land.country.EU else 'Drittland'}**"
                                )
                            elif i == int(anzahl_firmen) - 1:
                                column2.write(
                                    f"**Empfänger: {land.country.name} - {'EU' if land.country.EU else 'Drittland'}**"
                                )
                            else:
                                column2.write(
                                    f"**Zwischenhändler {i}: {land.country.name} - {'EU' if land.country.EU else 'Drittland'}**"
                                )
                            ust = column2.checkbox(
                                "Vom Heimatland abweichende USt-ID",
                                key=f"abweichende_ust_id_{i}",
                            )
                            if ust:
                                laender_ohne_eigenes = [
                                    l
                                    for l in laender
                                    if l.code != land.country.code and l.EU is True
                                ]
                                target_country_vat_id = column2.selectbox(
                                    f"Land der verwendeten USt-ID:",
                                    laender_ohne_eigenes,
                                    key=f"land_abweichende_ust_id_{i}",
                                )
                                land.set_changed_vat_id(target_country_vat_id)
                schritt = 1
            else:
                schritt = 0
        elif anzahl_firmen == 2:
            schritt = 0
            st.warning("Ein Reihengeschäft benötigt mindestens drei beteiligte Firmen.")
        elif anzahl_firmen < 2:
            schritt = 0
            st.error("Ein Handelsgeschäft benötigt mind. zwei beteiligte Firmen.")
    if schritt == 1:
        endanalyse_benötigte_daten = False
        with st.expander("Lieferung / Zollabwicklung"):
            st.subheader("Schritt 4: Lieferung")
            transport_firma: Handelsstufe | str = st.selectbox(
                "Welche Firma transportiert die Ware / veranlasst den Transport?",
                ["keine Auswahl"] + laender_firmen,
            )
            if isinstance(transport_firma, Handelsstufe):
                for firma in laender_firmen:
                    if firma.identifier == transport_firma.identifier:
                        firma.responsible_for_shippment = True
                        endanalyse_benötigte_daten = True
                        st.warning(
                            "Die transportierende Firma wird im Chart orange dargestellt.",
                            icon="✅",
                        )
                        break
            if transport_firma != "keine Auswahl" and "Z" in transport_firma.get_role_name():
                st.info(
                    f"Da der {transport_firma.get_role_name(True)} den Transport beauftragt, ist sein Status relevant.",
                    icon="ℹ️")
                intermediar = st.selectbox("Status", ["keine Auswahl", "Auftretender Lieferer", "Erwerber"])
                if intermediar != "keine Auswahl":
                    for firma in laender_firmen:
                        if firma.identifier == transport_firma.identifier:
                            match intermediar:
                                case "Auftretender Lieferer":
                                    firma.intermediary_status = IntermediaryStatus.OCCURING_SUPPLIER
                                    endanalyse_benötigte_daten = True
                                case "Erwerber":
                                    firma.intermediary_status = IntermediaryStatus.BUYER
                                    endanalyse_benötigte_daten = True
                                case _:
                                    raise ValueError("Unbekannter Intermediary Status")
                            break
                else:
                    endanalyse_benötigte_daten = False

            customs_necessary = all(
                laender_firmen[i].country.EU for i in range(len(laender_firmen))
            )
            if not customs_necessary:
                st.divider()
                st.subheader("Schritt 5: Zollabwicklung")

                customs_import = st.selectbox(
                    "Wer übernimmt die Zollabwicklung?",
                    ["keine Auswahl"] + laender_firmen,
                )
                if isinstance(customs_import, Handelsstufe):
                    for firma in laender_firmen:
                        if firma.identifier == customs_import.identifier:
                            firma.responsible_for_customs = True
                            endanalyse_benötigte_daten = True
                            st.success(
                                "Die Zoll abwickelnde Firma wird im Chart grün dargestellt.",
                                icon="✅",
                            )
                            break
                else:
                    endanalyse_benötigte_daten = False

            if endanalyse_benötigte_daten:
                st.divider()
                st.subheader("Schritt 6: Analyse")
                st.text(
                    "Vielen Dank. Nun sind alle Daten erfasst um den Sachverhalt korrekt berechnen zu können."
                )
                st.button(
                    "Analyse starten.",
                    icon="🛫",
                    on_click=helper_switch_page,
                    args=(1, laender_firmen),
                )

    if len(laender_firmen) > 2:
        diagram.subheader("Geschäftsablauf")
        transaction = Transaktion(laender_firmen[0], laender_firmen[-1])
        dot = Digraph(
            comment="Geschäftsablauf", graph_attr={"rankdir": "LR"}
        )  # LR für Left-to-Right-Layout
        # dot.attr(splines="ortho")
        with dot.subgraph() as s:
            s.attr("node", shape="box")
            for company in transaction.get_ordered_chain_companies():
                company_text = f"{company.get_role_name(True)}"
                # Zusatzinfos: Abw. USt-ID und Status
                zusatz_infos = []
                if company.changed_vat and company.new_country:
                    zusatz_infos.append(f"abw. USt-ID: {company.new_country.code}\n")
                if company.intermediary_status is not None:
                     zusatz_infos.append(f"Status: {company.get_intermideary_status()}\n")

                if zusatz_infos:
                    company_text += "\n" + "".join(zusatz_infos)
                else:
                      company_text += "\n--------\n " # Minimaler Platzhalter für Höhe
                company_text += f"{company.country.name}({company.country.code})"
                if company.country.EU:
                    company_text += ", EU"
                else:
                    company_text += ", Drittland"
                # Farbliche Markierung (Transporteur/Zoll)
                fillcolor = ""
                if company.responsible_for_shippment and company.responsible_for_customs:
                    fillcolor = "#ffa500:#b2d800" # Orange/Grün Gradient
                elif company.responsible_for_shippment:
                    fillcolor = "#ffa500" # Orange
                elif company.responsible_for_customs:
                    fillcolor = "#b2d800" # Grün

                if fillcolor:
                    s.node(
                        str(company.identifier),
                        company_text,
                        style="filled",
                        fillcolor=fillcolor
                    )
                else:
                     s.node(
                        str(company.identifier),
                        company_text
                    )

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

        st.header("Analyse des Reihengeschäfts")
        is_triangle = transaction.is_triangular_transaction()
        if is_triangle:
            st.success(
                """**Dreiecksgeschäft erkannt!**
				Die Voraussetzungen für die Vereinfachungsregelung nach § 25b UStG / Art. 141 MwStSystRL scheinen erfüllt zu sein.
				Beachten Sie die besonderen Rechnungslegungs- und Meldepflichten.
				""",
                icon="🔺",
            )
        try:
            # Berechnung durchführen (nur einmal)
            alle_lieferungen: list[Lieferung] = transaction.calculate_delivery_and_vat()
            st.subheader("Visualisierung: Lieferungen & Rechnungen")
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
                    if company.changed_vat and company.new_country:
                        company_text += f"\nabw. USt-ID: {company.new_country.code}"
                    s.node(str(company.identifier), company_text)

            # 2. Kanten (Rechnungen UND ruhende Lieferungen) erstellen
            bewegte_lieferung_gefunden: Lieferung | None = None
            for lief in alle_lieferungen:
                # --- Rechnungskante
                rechnungs_label = f"Rechnung:\n{lief.get_vat_treatment_display()}"
                if (
                    lief.invoice_note
                    and "Steuerfrei" not in lief.invoice_note
                    and "Reverse Charge" not in lief.invoice_note
                ):
                    rechnungs_label += f"\n({lief.invoice_note})"

                dot_analyse.edge(
                    str(lief.lieferant.identifier),
                    str(lief.kunde.identifier),
                    label=rechnungs_label,
                    color="orange",  # Farbe für Rechnungen
                    fontsize="10",
                    # constraint='false' # Kann helfen, Layout zu entzerren, wenn Kanten sich kreuzen
                )

                # --- Kante für Ruhende Lieferung ---
                if not lief.is_moved_supply:
                    ruhend_label = f"Ruhende Lieferung\nOrt: {lief.place_of_supply.code if lief.place_of_supply else '?'}"
                    dot_analyse.edge(
                        str(lief.lieferant.identifier),
                        str(lief.kunde.identifier),
                        label=ruhend_label,
                        color="grey",  # Andere Farbe für ruhende Lieferung
                        style="dashed",  # Gestrichelt zur Unterscheidung
                        fontsize="9",  # Etwas kleiner
                        # constraint='false' # Kann helfen, Layout zu entzerren
                    )
                else:
                    # Merke dir die bewegte Lieferung für die separaten Kanten
                    bewegte_lieferung_gefunden = lief

            # 3. Kante für die RECHTLICH bewegte Lieferung (BLAU)
            if bewegte_lieferung_gefunden:
                bewegte_label = f"Bewegte Lieferung\nOrt: {bewegte_lieferung_gefunden.place_of_supply.code if bewegte_lieferung_gefunden.place_of_supply else '?'}"
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
                transport_label = f"Physischer Transport\ndurch: {transaction.shipping_company.get_role_name(True)}"
                dot_analyse.edge(
                    # Von erster zu letzter Firma
                    str(transaction.start_company.identifier),
                    str(transaction.end_company.identifier),
                    label=transport_label,
                    color="green",  # Farbe für physischen Transport
                    style="bold, dotted",  # Fett und gepunktet zur Unterscheidung
                    fontsize="10",
                    splines="curved",  # Oder polyline, um Knoten zu umgehen
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
                    # Nutze die verbesserte __repr__ Methode der Lieferung
                    st.markdown(f"- {bewegte_lieferung}")
                else:
                    st.warning("Keine bewegte Lieferung gefunden.", icon="⚠️")

                # 2. Ruhende Lieferungen anzeigen
                st.markdown("#### Ruhende Lieferungen")
                ruhende_lieferungen = [
                    l for l in alle_lieferungen if not l.is_moved_supply
                ]
                if ruhende_lieferungen:
                    for lief in ruhende_lieferungen:
                        # Nutze die verbesserte __repr__ Methode der Lieferung
                        st.markdown(f"- {lief}")
                else:
                    st.info("Keine ruhenden Lieferungen vorhanden.")

            # --- Abschnitt Rechnungsstellung ---
            # Nur anzeigen, wenn die Berechnung erfolgreich war
            if alle_lieferungen:
                with st.expander(
                    "Übersicht der Rechnungsstellung", icon="📝", expanded=True
                ):
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
            if alle_lieferungen:  # Nur anzeigen, wenn Berechnung erfolgreich war
                registration_data = transaction.determine_registration_obligations()
                with st.expander(
                    "Mögliche Registrierungspflichten (EU)", icon="🇪🇺", expanded=False
                ):
                    st.markdown("#### Notwendige USt-Registrierungen pro Firma")
                    st.caption(
                        "Dies ist eine automatisierte Einschätzung basierend auf den Lieferungen. Die tatsächliche Notwendigkeit kann von weiteren Faktoren abhängen."
                    )

                    firma: Handelsstufe
                    registrierungen: set[Country]
                    for firma, registrierungen in registration_data.items():
                        # Überspringe Firmen ohne EU-Registrierungsbedarf oder Drittlandsfirmen ohne Bedarf
                        if not firma.country.EU and not registrierungen:
                            continue

                        st.markdown(
                            f"**{firma.get_role_name(True)}:**"
                        )  # Nutzt die __repr__ der Handelsstufe

                        # Heimatland immer anzeigen, wenn EU-Firma
                        home_country_registered = False
                        if firma.country.EU:
                            st.markdown(
                                f"- {firma.country.name} ({firma.country.code}) - *Heimatland (Annahme)*"
                            )
                            home_country_registered = True

                        # Zusätzliche Registrierungen auflisten
                        additional_registrations = registrierungen - {
                            firma.country
                        }  # Entferne Heimatland aus Set
                        if additional_registrations:
                            for country in sorted(
                                additional_registrations, key=lambda c: c.name
                            ):
                                st.markdown(
                                    f"- :red[{country.name} ({country.code}) - *Zusätzlich erforderlich*]"
                                )
                        elif (
                            not home_country_registered and not additional_registrations
                        ):
                            # Falls es eine Drittlandsfirma ohne Registrierungsbedarf ist
                            st.markdown(
                                "- *Keine EU-Registrierungspflicht aus dieser Transaktion ersichtlich.*"
                            )
                        elif home_country_registered and not additional_registrations:
                            # Falls nur Heimatland-Registrierung nötig ist
                            st.markdown(
                                "- *Keine zusätzlichen EU-Registrierungen erforderlich.*"
                            )
                        if firma != transaction.end_company:
                            st.divider()

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
