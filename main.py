import streamlit as st

if __name__ == "__main__":
    st.set_page_config("USt-Reihengeschäfte", layout="wide")
    uebersicht = st.Page(
        "submodules/0_Uebersicht.py",
        title="Übersicht",
        icon=":material/dashboard_customize:",
    )
    ust_reihen = st.Page(
        "submodules/1_USt-Reihen.py",
        title="Reihengeschäfte",
        icon=":material/monetization_on:",
    )
    impressum = st.Page(
        "submodules/2_Impressum.py", title="Impressum", icon=":material/info:"
    )
    haftungsauschluss = st.Page(
        "submodules/3_Haftungsauschluss.py",
        title="Haftungsauschluss",
        icon=":material/info:",
    )
    pages = {
        "Allgemeines": [uebersicht],
        "Rechtliches": [impressum, haftungsauschluss],
    }
    if "HaftungsauschlussAkzeptiert" in st.session_state:
        pages = {
            "Allgemeines": [uebersicht],
            "USt": [ust_reihen],
            "Rechtliches": [impressum, haftungsauschluss],
        }
    pg = st.navigation(pages)
    pg.run()
