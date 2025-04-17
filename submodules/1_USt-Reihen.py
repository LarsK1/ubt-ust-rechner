import streamlit as st
from helpers.helpers import get_countries, Handelsstufe, Transaktion
from helpers.fixed_header import st_fixed_container
from graphviz import Digraph
from random import randrange

st.title("USt-Reihengeschäfte")

laender_firmen: list[Handelsstufe] = []

# Liste der verfügbaren Länder auf Deutsch
laender = get_countries()
schritt = 0

diagram = st_fixed_container(mode="sticky", position="top", border=True, margin="0px")

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
    with st.expander("Bewegte und ruhende Lieferung"):
        st.subheader("Schritt 4: Lieferung")
        transport_firma: Handelsstufe | str = st.selectbox(
            "Welche Firma transportiert die Ware / veranlasst den Transport?",
            ["keine Auswahl"] + laender_firmen,
        )
        if isinstance(transport_firma, Handelsstufe):
            for firma in laender_firmen:
                if firma.identifier == transport_firma.identifier:
                    firma.responsible_for_shippment = True
                    st.warning(
                        "Die transportierende Firma wird im Chart orange dargestellt.",
                        icon="✅",
                    )
                    break
        if transport_firma != "keine Auswahl":
            erhaltende_firma_laender_moeglich = [
                l for l in laender_firmen if l.identifier != transport_firma.identifier
            ]
        else:
            erhaltende_firma_laender_moeglich = laender_firmen
        if not all(laender_firmen[i].country.EU for i in range(len(laender_firmen))):
            st.divider()
            st.subheader("Schritt 5: Zollabwicklung")

            customs_import = st.selectbox(
                "Wer übernimmt die Zollabwicklung?", ["keine Auswahl"] + laender_firmen
            )
            if isinstance(customs_import, Handelsstufe):
                for firma in laender_firmen:
                    if firma.identifier == customs_import.identifier:
                        firma.responsible_for_customs = True
                        st.success(
                            "Die Zoll abwickelnde Firma wird im Chart grün dargestellt.",
                            icon="✅",
                        )
                        break

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
            if company.changed_vat:
                company_text = (
                    str(company)
                    .replace("-", "\n-------\n", 1)
                    .replace("-------", f"abw. USt-ID: {company.new_country}")
                )
            else:
                company_text = str(company).replace("-", "\n-------\n", 1)
            if not company.country.EU:
                company_text += ", Drittland"
            else:
                company_text += ", EU"
            if company.responsible_for_shippment and company.responsible_for_customs:
                s.attr("node", shape="box", fillcolor="#ffa500:#b2d800", style="filled")
                s.node(
                    str(company.identifier),
                    company_text,
                )
                s.attr("node", shape="box", style="", color="")
            elif company.responsible_for_shippment:
                s.attr("node", shape="box", fillcolor="#ffa500", style="filled")
                s.node(
                    str(company.identifier),
                    company_text,
                )
                s.attr("node", shape="box", style="", color="")
            elif company.responsible_for_customs:
                s.attr("node", shape="box", fillcolor="#b2d800", style="filled")
                s.node(
                    str(company.identifier),
                    company_text,
                )
                s.attr("node", shape="box", style="", color="")
            else:
                s.node(
                    str(company.identifier),
                    company_text,
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
        if transaction.shipping_company == transaction.start_company:
            dot.edge(
                str(transaction.start_company.identifier),
                str(transaction.end_company.identifier),
                f"Transport durch {transaction.shipping_company}",
                style="bold",
                color="blue",
                splines="polyline",
            )
        elif transaction.shipping_company == transaction.end_company:
            dot.edge(
                str(transaction.start_company.identifier),
                str(transaction.end_company.identifier),
                f"Transport durch {transaction.shipping_company}",
                style="bold",
                color="blue",
                splines="polyline",
            )
        else:
            dot.edge(
                str(transaction.start_company.identifier),
                str(transaction.end_company.identifier),
                f"Transport durch {transaction.shipping_company}",
                style="bold",
                color="blue",
                splines="polyline",
            )

    diagram.graphviz_chart(dot, use_container_width=True)
