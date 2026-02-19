import pandas as pd
import streamlit as st 

from database import db_conn, init_database, insert_aircraft
from scraper import scrape_page

st.set_page_config(layout="wide")

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

def brand_selectbox(df):
    brands = pd.read_sql_query("""
        SELECT DISTINCT brand
        FROM aircraft
        WHERE active = 1
        ORDER BY brand
        """, conn)
    
    return brands

init_database()

with db_conn() as conn:
    df = pd.read_sql_query("SELECT * FROM aircraft WHERE active = 1", conn)

st.title("Helicopter market-dashboard")

col_1, col_2, = st.columns([0.3, 0.7], border=True)

with col_1:
    st.markdown(":blue-background[Listing overview]")
    chart_df = df.groupby("brand").size().reset_index(name="Listings")
    chart_df = chart_df.rename(columns={"brand": "Brand"})
    st.bar_chart(chart_df, x="Brand", y="Listings")

with col_2:
    col_3, col_4 = st.columns([0.35, 0.65], border=True)

    with col_3:
        st.markdown(":blue-background[Filter]")
        brands = brand_selectbox(df)
        selected_brand = st.selectbox(
            "Brand",
            brands, 
            index=None, 
            placeholder="Select brand..."
        )

        if selected_brand is None:
            pass
        else:   
            brand_df = df[df["brand"] == selected_brand].copy()
            brand_df["eur_price"] = pd.to_numeric(brand_df["eur_price"], errors="coerce")
            brand_df = brand_df.dropna(subset=["eur_price"])
            max_price = int(brand_df["eur_price"].max())
            price_range = st.slider("Price range", 0, max_price, (0, max_price))
            

    with col_4:
        st.write(":blue-background[Results]")

col_5, col_6 = st.columns(2, border=True)

with col_5:
    st.write("Under construction")

with col_6:
    st.markdown(":blue-background[Raw data]")
    dataframe(df)

with st.container(border=True):
        col_left, col_right = st.columns([1, 1], vertical_alignment="center")
        with col_left:

            if "update_ok" not in st.session_state:
                st.session_state.update_ok = False

            if st.button("Update data"):
                st.session_state.update_ok = False
                try:
                    with st.spinner("Getting data..."):
                        aircrafts, run_time = scrape_page()
                        insert_aircraft(aircrafts, run_time)
                    st.session_state.update_ok = True
                    st.rerun()
                except:
                    st.error(":red-background[Error]")

            if st.session_state.update_ok:
                st.toast(":green-background[Data updated successfully]")
        
        with col_right:
            ts = pd.to_datetime(df["timestamp"]).max()
            pretty = ts.strftime("%d.%m.%Y %H:%M")
            st.markdown(
                 f"<div style='text-align: right;'>Last data update: {pretty}</div>",
                unsafe_allow_html=True,
            )

