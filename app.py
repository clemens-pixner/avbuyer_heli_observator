import pandas as pd
import sqlite3
import streamlit as st 

from database import init_database, clear_db, insert_aircraft
from scraper import scrape_page

st.set_page_config(layout="wide")

init_database()

if st.button("Scrape data"):
    with st.spinner("Scraping..."):
        aircrafts = scrape_page()
        
        if aircrafts:
            clear_db()
            insert_aircraft(aircrafts)
            st.success(f"{len(aircrafts)} listings loaded.")
            st.rerun()
        else:
            st.warning("No data found")


conn = sqlite3.connect("aircraft.db")
df = pd.read_sql("SELECT brand FROM aircraft", conn)
conn.close()

