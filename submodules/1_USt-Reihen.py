import streamlit as st
from helpers.helpers import get_countries, Handelsstufe
from graphviz import Digraph

st.title("USt-Reihengeschäfte")

# Liste der verfügbaren Länder auf Deutsch
laender = get_countries()
schritt = 0


with st.expander("Grundlegende Daten"):
    st.subheader("Schritt 1: Beteiligte Firmen und Länderauswahl")
    # Anzahl der beteiligten Firmen festlegen
    anzahl_firmen = st.number_input(
        "Anzahl der beteiligten Firmen:", min_value=1, step=1, value=3
    )
    if anzahl_firmen > 2:
        st.divider()
        # Länderauswahl für jede Firma
        if anzahl_firmen:
            st.subheader("Schritt 2: Wähle das Land für jede Firma")
            laender_firmen = []
            for i in range(int(anzahl_firmen)):
                if i == 0:
                    land = st.selectbox(f"Verkäufer:", laender, key=f"firma_{i}")
                elif i == anzahl_firmen - 1:
                    land = st.selectbox(f"Empfänger:", laender, key=f"firma_{i}")
                else:
                    land = st.selectbox(
                        f"Zwischenhändler {i}:", laender, key=f"firma_{i}"
                    )
                laender_firmen.append(Handelsstufe(land, i, int(anzahl_firmen)))
            st.divider()
            # Ausgabe der ausgewählten Länder
            if laender_firmen:
                st.subheader("Schritt 3: Besondere Merkmale der Firmen")
                for i, land in enumerate(laender_firmen):
                    land: Handelsstufe
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
                            l for l in laender if l.code != land.country.code
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
        transport_firma: Handelsstufe = st.selectbox(
            "Welche Firma transportiert die Ware?", ["keine Auswahl"] + laender_firmen
        )
        if isinstance(transport_firma, Handelsstufe):
            transport_firma.is_supplier = True
        if transport_firma != "keine Auswahl":
            erhaltende_firma_laender_moeglich = [
                l for l in laender_firmen if l.identifier != transport_firma.identifier
            ]
        else:
            erhaltende_firma_laender_moeglich = laender_firmen

        erhaltende_firma = st.selectbox(
            "Welche Firma erhält die Ware?",
            ["keine Auswahl"] + erhaltende_firma_laender_moeglich,
        )
        if isinstance(erhaltende_firma, Handelsstufe):
            erhaltende_firma.is_receiver = True

        customs_import = st.selectbox(
            "Wer übernimmt die Zollabwicklung?", ["keine Auswahl"] + laender_firmen
        )
        if isinstance(customs_import, Handelsstufe):
            customs_import.responsible_for_customs = True
