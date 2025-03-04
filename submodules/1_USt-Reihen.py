import streamlit as st
import pycountry
import gettext

german = gettext.translation('iso3166-1', pycountry.LOCALES_DIR, languages=['de'])
german.install()

st.title("USt-Reihengeschäfte")

st.subheader("Beteiligte Firmen und Länderauswahl")
# Liste der verfügbaren Länder auf Deutsch
laender = [_(country.name) for country in pycountry.countries]
#Test
# Anzahl der beteiligten Firmen festlegen
anzahl_firmen = st.number_input("Anzahl der beteiligten Firmen:", min_value=1, step=1)

# Länderauswahl für jede Firma
if anzahl_firmen:
    st.write("Wähle das Land für jede Firma:")
    laender_firmen = []
    for i in range(int(anzahl_firmen)):
        land = st.selectbox(f"Firma {i+1}:", laender, key=f"firma_{i}")
        laender_firmen.append(land)

    # Ausgabe der ausgewählten Länder
    if laender_firmen:
        st.write("Ausgewählte Länder für die Firmen:")
        for i, land in enumerate(laender_firmen):
            st.write(f"Firma {i+1}: {land}")

        # Reihenbesteuerungslogik (Platzhalter)
        st.subheader("Umsatzsteuerliche Analyse")
        st.write("Hier wird die umsatzsteuerliche Analyse durchgeführt.")

        # Beispiel für die Ausgabe von Ergebnissen (Platzhalter)
        for i, land in enumerate(laender_firmen):
            st.write(f"Umsatzsteuerliche Behandlung für Firma {i+1} in {land}:")
            # Hier müsste deine Logik zur Berechnung der Umsatzsteuer stehen
            # Basierend auf den Umsatzsteuergesetzen der ausgewählten Länder
            st.write("Ergebnis: [Umsatzsteuerbetrag oder relevante Information]")

        # Zusätzliche Informationen oder Zusammenfassung (Platzhalter)
        st.subheader("Zusammenfassung")
        st.write("Hier könnte eine Zusammenfassung der umsatzsteuerlichen Analyse stehen.")
        st.write("Weitere Informationen: [Relevante Links oder Dokumente]")

# Hier kann Code für die Speicherung/Ausgabe von Daten stehen