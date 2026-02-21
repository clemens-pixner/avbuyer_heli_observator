import altair as alt
import pandas as pd
import streamlit as st

from database import db_conn, init_database, insert_aircraft
from scraper import scrape_page

st.set_page_config(layout="wide")

def dataframe(df):
    show_df = df.drop(
        columns=["aircraft_id", "timestamp", "active"]
    ).copy()

    eur_mask = show_df["eur_price"].notna()
    fp_mask = show_df["foreign_price"].notna()

    show_df.loc[eur_mask, "eur_price"] = (
        "€ "
        + show_df.loc[eur_mask, "eur_price"].map("{:,.0f}".format).str.replace(",", ".", regex=False)
    )

    show_df.loc[fp_mask, "foreign_price"] = (
        show_df.loc[fp_mask, "currency"] + " "
        + show_df.loc[fp_mask, "foreign_price"].map("{:,.0f}".format).str.replace(",", ".", regex=False)
    )

    show_df = show_df.drop(columns=["currency"])

    return st.dataframe(
        show_df,
        column_config={
            "url": st.column_config.LinkColumn("URL", display_text="url"),
        },
        width="stretch",
    )

def brand_selectbox(df):
    return (
        df["brand"]
        .dropna()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

init_database()

with db_conn() as conn:
    df = pd.read_sql_query("SELECT * FROM aircraft WHERE active = 1", conn)

st.title("Helicopter market-dashboard")

col_1, col_2 = st.columns([0.3, 0.7], border=True)

with col_1:
    st.markdown("**Listing overview**")
    st.write("")

    chart_df = (
        df.groupby("brand")
        .size()
        .reset_index(name="Listings")
        .rename(columns={"brand": "Brand"})
    )

    chart = (
        alt.Chart(chart_df)
        .mark_bar(color="#226597")
        .encode(
            x=alt.X("Brand:N"),
            y=alt.Y("Listings:Q"),
            tooltip=["Brand:N", "Listings:Q"],
        )
        .properties(height=320)
    ).configure_axis(labelColor="#113F67", titleColor="#113F67")

    st.altair_chart(chart, use_container_width=True)

with col_2:
    col_3, col_4 = st.columns([0.35, 0.65], border=True, vertical_alignment="top")

    with col_3:
        brands_raw = brand_selectbox(df)
        if isinstance(brands_raw, pd.DataFrame):
            brands = brands_raw.iloc[:, 0].dropna().tolist()
        else:
            brands = list(brands_raw)

        selected_brand = st.selectbox(
            "**Brand**",
            brands,
            index=None,
            placeholder="Select brand..."
        )
        no_brand_selected = selected_brand is None

        brand_df = pd.DataFrame(columns=["listing_no", "model", "price", "listing_key"])
        max_price = 10_000_000

        if not no_brand_selected:
            brand_df = df[df["brand"] == selected_brand].copy()
            brand_df["eur_price"] = pd.to_numeric(brand_df["eur_price"], errors="coerce")
            brand_df = brand_df.dropna(subset=["model", "eur_price"]).reset_index(drop=True)
            brand_df["listing_no"] = brand_df.index + 1
            brand_df["price"] = brand_df["eur_price"]
            brand_df["listing_key"] = brand_df["listing_no"].astype(str) + " | " + brand_df["model"].astype(str)
            if not brand_df.empty:
                max_price = int(brand_df["price"].max())

        if "price_range" not in st.session_state:
            st.session_state.price_range = (0, max_price)
        if "prev_price_toggle" not in st.session_state:
            st.session_state.prev_price_toggle = False

        lo, hi = st.session_state.price_range
        lo = max(0, min(int(lo), max_price))
        hi = max(0, min(int(hi), max_price))
        if lo > hi:
            lo, hi = 0, max_price
        st.session_state.price_range = (lo, hi)

        price_toggle = st.toggle(
            "Filter by price",
            value=False,
            disabled=no_brand_selected
        )

        if st.session_state.prev_price_toggle and not price_toggle:
            st.session_state.price_range = (0, max_price)

        st.session_state.prev_price_toggle = price_toggle

        price_range = st.slider(
            "Price range",
            min_value=0,
            max_value=max_price,
            value=st.session_state.price_range,
            step=50_000,
            format="€%d",
            key="price_range",
            disabled=no_brand_selected or (not price_toggle)
        )

        if price_toggle:
            min_selected, max_selected = price_range
        else:
            min_selected, max_selected = 0, max_price

        threshold = max_selected

        if no_brand_selected:
            price_filtered_df = pd.DataFrame(columns=["listing_no", "model", "price", "listing_key"])
        else:
            price_filtered_df = brand_df[brand_df["price"] >= min_selected].copy().sort_values("listing_no")

        hide_toggle = st.toggle(
            "Hide objects",
            value=False,
            disabled=no_brand_selected,
            key="hide_objects_toggle"
        )

        hidden_indices = []
        editor_source = pd.DataFrame(columns=["Hide", "Index", "Model"])

        if not no_brand_selected and not price_filtered_df.empty:
            hidden_map_key = f"hidden_map_{selected_brand}"
            if hidden_map_key not in st.session_state:
                st.session_state[hidden_map_key] = {}
            hidden_map = st.session_state[hidden_map_key]

            editor_source = price_filtered_df[["listing_no", "model"]].rename(
                columns={"listing_no": "Index", "model": "Model"}
            ).copy()
            editor_source.insert(
                0,
                "Hide",
                editor_source["Index"].astype(int).map(lambda i: hidden_map.get(int(i), False))
            )

        editor_disabled = True if (no_brand_selected or not hide_toggle) else ["Index", "Model"]

        with st.popover("Objects to hide", use_container_width=True):
            edited_hide_df = st.data_editor(
                editor_source,
                hide_index=True,
                use_container_width=True,
                disabled=editor_disabled,
                key=f"hide_editor_{selected_brand if selected_brand is not None else 'none'}",
                column_config={
                    "Hide": st.column_config.CheckboxColumn("Hide"),
                    "Index": st.column_config.NumberColumn("Index", format="%d"),
                    "Model": st.column_config.TextColumn("Model"),
                },
            )

        if not no_brand_selected and not editor_source.empty:
            hidden_map_key = f"hidden_map_{selected_brand}"
            hidden_map = st.session_state[hidden_map_key]
            for _, row in edited_hide_df.iterrows():
                hidden_map[int(row["Index"])] = bool(row["Hide"])
            if hide_toggle:
                hidden_indices = edited_hide_df.loc[edited_hide_df["Hide"], "Index"].astype(int).tolist()

with col_4:
    st.write("**Market situation**")

    if selected_brand is None:
        st.info("Select a brand to display data.")
    else:
        plot_df = price_filtered_df.copy()
        if hide_toggle and hidden_indices:
            plot_df = plot_df[~plot_df["listing_no"].isin(hidden_indices)]
        plot_df = plot_df.sort_values("listing_no")

        if plot_df.empty:
            st.info("Keine Modelle im gewählten Bereich.")
        else:
            plot_df["base_top"] = plot_df["price"].clip(upper=threshold)
            sort_order = plot_df["listing_key"].tolist()

            x_enc = alt.X(
                "listing_key:N",
                sort=sort_order,
                title="Listing / Model"
            )

            bars = alt.Chart(plot_df).mark_bar(color="#226597").encode(
                x=x_enc,
                y=alt.Y("base_top:Q", title="Price (€)"),
                tooltip=[
                    alt.Tooltip("model:N", title="Model"),
                    alt.Tooltip("price:Q", title="Price", format=",.0f"),
                ],
            )

            highlight = (
                alt.Chart(plot_df)
                .transform_filter(alt.datum.price > threshold)
                .mark_bar(color="#87C0CD")
                .encode(
                    x=x_enc,
                    y=alt.Y("price:Q"),
                    y2=alt.Y2("base_top:Q"),
                )
            )

            rule_df = pd.DataFrame({"threshold": [threshold]})
            rule = alt.Chart(rule_df).mark_rule(color="#2E073F", strokeDash=[6, 4]).encode(
                y="threshold:Q"
            )

            layered = alt.layer(bars, highlight, rule).properties(height=360)
            layered = layered.configure_axis(labelColor="#113F67", titleColor="#113F67")
            st.altair_chart(layered, use_container_width=True)

col_5, col_6 = st.columns(2, border=True)

with col_5:
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
            except Exception as e:
                st.error(f"Error {e}")

        if st.session_state.update_ok:
            st.toast(":green-background[Data updated successfully]")
            st.session_state.update_ok = False

    with col_right:
        ts = pd.to_datetime(df["timestamp"]).max()
        pretty = ts.strftime("%d.%m.%Y %H:%M")
        st.caption(
            f"<div style='text-align: right;'>Last data update: {pretty}</div>",
            unsafe_allow_html=True,
        )

with col_6:
    st.markdown("**Raw data**")
    dataframe(df)

    