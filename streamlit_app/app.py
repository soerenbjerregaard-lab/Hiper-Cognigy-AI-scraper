import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(
    page_title="Chatbot-kvalitet",
    page_icon="📊",
    layout="wide",
)

pg = st.navigation([
    st.Page("pages/home.py",                             title="📊 Oversigt",              icon="📊", default=True),
    st.Page("pages/1_🔍_Scenario_Compare.py",            title="🔍 Sammenlign scenarier",  icon="🔍"),
    st.Page("pages/2_💬_Conversation_Explorer.py",       title="💬 Samtaleudforsker",      icon="💬"),
    st.Page("pages/3_📈_Question_Deep_Dive.py",          title="📈 Spørgsmålsanalyse",     icon="📈"),
    st.Page("pages/4_🔗_Dead_Links.py",                  title="🔗 Døde links",            icon="🔗"),
])
pg.run()
