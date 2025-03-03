import streamlit as st

if __name__ == "__main__":
	st.set_page_config(
		"USt-Reihengeschäfte",
		layout="wide"
	)
	uebersicht = st.Page("submodules/0_Uebersicht.py", title="Übersicht", icon=":material/dashboard_customize:")
	ust_reihen = st.Page("submodules/1_USt-Reihen.py", title="USt-Reihen", icon=":material/monetization_on:")
	pages = {"Allgemein": [uebersicht], "USt": [ust_reihen,]}
	pg = st.navigation(pages)
	pg.run()