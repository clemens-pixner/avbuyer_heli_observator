import pandas as pd
import streamlit as st 

from database import db_conn, init_database, insert_aircraft
from scraper import scrape_page

def dataframe(df):
    show_df = df.drop(columns=["aircraft_id", "timestamp", "active"]).copy()

    eur_mask = show_df["eur_price"].notna()
    fp_mask = show_df["foreign_price"].notna()

    show_df.loc[eur_mask, "eur_price"] = (
    "€ " +
    show_df.loc[eur_mask, "eur_price"].map("{:,.0f}".format).str.replace(",", ".", regex=False)
    )

    show_df.loc[fp_mask, "foreign_price"] = (
        show_df.loc[fp_mask, "currency"] + " " +
        show_df.loc[fp_mask, "foreign_price"].map("{:,.0f}".format).str.replace(",", ".", regex=False)
    )

    show_df = show_df.drop(columns=["currency"])

    return st.dataframe(
            show_df,
            column_config={
                "url": st.column_config.LinkColumn(
                    "URL",
                    display_text="url" 
                ),
                
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
    chart_df = df.groupby("brand").size().reset_index(name="Listings")
    chart_df = chart_df.rename(columns={"brand": "Brand"})
    st.bar_chart(chart_df, x="Brand", y="Listings")

with col_2:
    st.markdown(":blue-background[Raw data]")
    dataframe(df)

with st.container(border=True):
        col_left, col_right = st.columns([1, 1], vertical_alignment="center")
        with col_left:
            if st.button("Update data"):
                aircrafts, run_time = scrape_page()
                insert_aircraft(aircrafts, run_time)
                st.rerun()
        
        with col_right:
            ts = pd.to_datetime(df["timestamp"]).max()
            pretty = ts.strftime("%d.%m.%Y %H:%M")
            st.markdown(
                 f"<div style='text-align: right;'>Last data update: {pretty}</div>",
                unsafe_allow_html=True,
            )