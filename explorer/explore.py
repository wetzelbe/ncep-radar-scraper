import streamlit as st

st.set_page_config(layout="wide")

pg = st.navigation([st.Page("explore_pages/overview.py", title="Overview", icon=":material/house:"), 
                    st.Page("explore_pages/plot_single.py", title="Raw dataset", icon=":material/search:")])
pg.run()
