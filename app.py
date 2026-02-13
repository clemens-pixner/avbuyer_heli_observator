import pandas as pd
import sqlite3
import streamlit as st 

from database import init_database, insert_aircraft
from scraper import scrape_page

df = pd.read_sql_table()
#aircrafts, run_time = scrape_page()

st.title("Helicopter market-dashboard")
st.dataframe(data=df)
with st.sidebar:
    if st.button("Scrape"):
        #init_database()
        #insert_aircraft(aircrafts, run_time)
        st.write("Hello")
