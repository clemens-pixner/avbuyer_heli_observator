import pandas as pd
import streamlit as st 

from database import db_conn, init_database, insert_aircraft
from scraper import scrape_page

def dataframe(df):
    show_df = df.drop(columns=["aircraft_id", "timestamp", "active"])

    return st.dataframe(
            show_df,
            column_config={
                "url": st.column_config.LinkColumn(
                    "URL",
                    display_text="url" 
                )
            },
            width="stretch"
        )

init_database()

with db_conn() as conn:
    df = pd.read_sql_query("SELECT * FROM aircraft WHERE active = 1", conn)

st.title("Helicopter market-dashboard")

col_1, col_2 = st.columns(2, border=True)

with col_1:
    st.markdown(":blue-background[Chart]")
    st.bar_chart()

with col_2:
    st.markdown(":blue-background[Raw data]")
    dataframe(df)

with st.container(border=True, width="stretch", horizontal=True):
        if st.button("Scrape"):
            aircrafts, run_time = scrape_page()
            insert_aircraft(aircrafts, run_time)
            st.rerun()

        st.space("stretch")
        st.markdown(":grey-background[Last scrape:]")