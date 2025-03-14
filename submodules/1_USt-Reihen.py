import streamlit as st
import pycountry
from helpers.helpers import get_countries
from helpers.countries import Country

st.title("USt-Reihengeschäfte")


# Liste der verfügbaren Länder auf Deutsch
laender = get_countries()
schritt = 0

with st.expander("Grundlegende Daten"):
    st.subheader("Schritt 1: Beteiligte Firmen und Länderauswahl")
    # Anzahl der beteiligten Firmen festlegen
    anzahl_firmen = st.number_input(
        "Anzahl der beteiligten Firmen:", min_value=1, step=1
    )
    if anzahl_firmen > 2:
        st.divider()
        # Länderauswahl für jede Firma
        if anzahl_firmen:
            st.subheader("Schritt 2: Wähle das Land für jede Firma")
            laender_firmen = []
            for i in range(int(anzahl_firmen)):
                land = st.selectbox(f"Firma {i+1}:", laender, key=f"firma_{i}")
                laender_firmen.append(land)
            st.divider()
            # Ausgabe der ausgewählten Länder
            if laender_firmen:
                st.subheader("Schritt 3: Besondere Merkmale der Firmen")
                for i, land in enumerate(laender_firmen):
                    land: Country
                    container_land = st.container(border=True)
                    coulumn1, column2 = container_land.columns(
                        (
                            1,
                            4,
                        )
                    )
                    if land.flag:
                        coulumn1.image(land.flag, use_container_width=True)
                    column2.write(
                        f"**{i+1}: {land.name} - {'EU' if land.EU else 'Drittland'}**"
                    )
                    ust = column2.checkbox(
                        "Vom Heimatland abweichende USt-ID",
                        key=f"abweichende_ust_id_{i}",
                    )
                    if ust:
                        laender_ohne_eigenes = [
                            l for l in laender if l.code != land.code
                        ]
                        column2.selectbox(
                            f"Land der verwendeten USt-ID:",
                            laender_ohne_eigenes,
                            key=f"land_abweichende_ust_id_{i}",
                        )
            schritt = 1
        else:
            schritt = 0
    elif anzahl_firmen == 2:
        st.warning("Ein Reihengeschäft benötigt mindestens drei beteiligte Firmen.")
    elif anzahl_firmen < 2:
        st.error("Ein Handelsgeschäft benötigt mind. zwei beteiligte Firmen.")
if schritt == 1:
    with st.expander("Bewegte und ruhende Lieferung"):
        st.selectbox("Welche Firma transportiert die Ware?", laender_firmen)
        st.selectbox("Welche Firma erhält die Ware?", laender_firmen)
