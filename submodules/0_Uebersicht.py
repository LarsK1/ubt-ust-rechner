import streamlit as st

st.title("Übersicht")

st.write(
    """
## Einführung in den USt-Reihengeschäfts-Rechner

Der **USt-Reihengeschäfts-Rechner** ist ein webbasiertes Tool, das entwickelt wurde, um komplexe umsatzsteuerliche Reihengeschäfte zu analysieren und die korrekte Besteuerung zu berechnen. Diese Anwendung basiert auf **Streamlit**, einem Framework zur Erstellung von Datenanwendungen in Python.

### Zweck der Steuertools

1. **Analyse von Reihengeschäften**:
   - Die Tools ermöglichen es, die umsatzsteuerliche Behandlung von Reihengeschäften mit mehreren beteiligten Firmen zu analysieren.
   - Sie berücksichtigen die relevanten Regelungen des deutschen Umsatzsteuergesetzes sowie die EU-Richtlinien.

2. **Berechnung der Umsatzsteuer**:
   - Die Tools berechnen die korrekten Umsatzsteuerbeträge für jede Transaktion innerhalb des Reihengeschäfts.
   - Sie bieten eine übersichtliche Darstellung der Ergebnisse und relevanten Informationen.

### Weiterentwicklung

Diese Steuertools sind noch in der Entwicklung und werden kontinuierlich erweitert, um zusätzliche Funktionen und Verbesserungen zu integrieren. Ziel ist es, eine umfassende Lösung für die umsatzsteuerliche Behandlung von Reihengeschäften bereitzustellen.

Bleiben Sie gespannt auf zukünftige Updates und Erweiterungen!
"""
)

if "HaftungsauschlussAkzeptiert" not in st.session_state:
    st.divider()
    st.error("Der Haftungsauschluss wurde noch nicht akzeptiert.", icon="❌")
    if st.checkbox(
        "Hiermit erkenne ich den Haftungsauschluss an. Ohne eine Anerkennung ist die Nutzung dieses Tools nicht möglich."
    ):
        st.session_state["HaftungsauschlussAkzeptiert"] = True
        st.rerun()
else:
    st.divider()
    st.success("Der Haftungsauschluss wurde akzeptiert.", icon="✅")
    if not st.checkbox(
        "Hiermit erkenne ich den Haftungsauschluss an. Ohne eine Anerkennung ist die Nutzung dieses Tools nicht möglich.",
        value=True,
    ):
        del st.session_state["HaftungsauschlussAkzeptiert"]
        st.rerun()
