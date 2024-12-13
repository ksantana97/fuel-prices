import datetime
import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
import os
import folium
import json

from folium import CustomIcon
from data import geo_data
from utils import retrieve_data_app, InfoSelect, create_basis_map, add_station_map, ext_mom_key

curr_dt = datetime.datetime.now()
curr_mom_key = ext_mom_key(curr_dt.hour
                           )
data = retrieve_data_app(curr_mom_key)
info_select = InfoSelect(data)


st.set_page_config(
    page_title="Tu gasolinera más barata",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded",
)

alt.themes.enable("dark")

with st.sidebar:
    st.title("⛽ Encuentra tu gasolinera más barata hoy")

    geo_lvl_lst = ["COMUNIDAD AUTÓNOMA", "PROVINCIA", "ISLA", "MUNICIPIO"]
    selected_geo_lvl = st.selectbox(
        "Selecciona un nivel geográfico", geo_lvl_lst, index=0
    )

    ent_lst = info_select.get_distinct_geo_ent_lvls(selected_geo_lvl)
    selected_geo_ent_lvl = st.selectbox("Selecciona el lugar", ent_lst)

    info_select.set_geo_ent(selected_geo_ent_lvl)
    info_select.ref_info()

    brand_list = ["TODAS", "BP", "CEPSA", "DISA", "REPSOL", "SHELL", "OTRAS"]
    selected_brand = st.selectbox("Selecciona una marca", brand_list, index=0)

    info_select.set_brand(selected_brand)
    info_select.ref_info()

    products_list = [
        "BIODIÉSEL",
        "BIOETANOL",
        "GNC",
        "GNL",
        "GLP",
        "GASÓLEO A",
        "GASÓLEO B",
        "GASÓLEO PREMIUM",
        "GASOLINA 95",
        "GASOLINA 98",
        "HIDRÓGENO",
    ]
    selected_product = st.selectbox("Selecciona un producto", products_list, index=8)

    info_select.set_prod(selected_product)
    info_select.ref_info()


col = st.columns((0.6, 0.4), gap="medium")

with col[0]:
    st.header("Precios", divider=True)
    col1, col2, col3 = st.columns(3)
    kpis = info_select.get_kpis()
    col1.metric(label="Precio más caro", value=kpis["max"]["value"], delta=kpis["max"]["delta"])
    col2.metric(label="Precio medio", value=kpis["mean"]["value"], delta=kpis["mean"]["delta"])
    col3.metric(label="Precio más barato", value=kpis["min"]["value"], delta=kpis["min"]["delta"])

    st.header("Localízalas en tu mapa", divider=True)

    m = create_basis_map(
        geo_data[selected_geo_ent_lvl]["latitud"],
        geo_data[selected_geo_ent_lvl]["longitud"],
        geo_data[selected_geo_ent_lvl]["zoom"],
    )

    # Mostrar el mapa en Streamlit
    current_stations_df = info_select.current_df[
        ["StationName", "StationLatitude", "StationLongitude"]
    ].drop_duplicates()

    for index, row in current_stations_df.iterrows():
        add_station_map(row, m)

    # Renderizar el mapa como HTML
    mapa_html = m._repr_html_()

    # Mostrar el mapa en Streamlit
    st.components.v1.html(mapa_html, height=500)

with col[1]:
    st.header("Top 10 más baratas", divider=True)
    top_10_df = info_select.get_top_n_cheapest_stat(10)
    st.dataframe(
        top_10_df,
        column_order=("StationName", "Price"),
        hide_index=True,
        width=None,
        column_config={
            "StationName": st.column_config.TextColumn(
                "Estaciones de servicio", width="Small"
            ),
            "Price": st.column_config.ProgressColumn(
                "Precio",
                format="%f",
                min_value=0,
                max_value=max(top_10_df.Price),
                width="small",
            ),
        },
    )
    with st.expander("Información relevante", expanded=True):
        st.write(
            """
            - Datos: [Precio de carburantes en las gasolineras españolas](<https://datos.gob.es/es/catalogo/e05068001-precio-de-carburantes-en-las-gasolineras-espanolas>). La información se extrae en 5 momentos del día: madrugada, mañana, mediodía, tarde y noche. La mostrada es la última información disponible.
            - :orange[**Precios**]: Precio máximo, mínimo y medio, junto a comparación con la información promedia de los últimos 7 días.
            - :orange[**Top 10 más baratas**]: se muestra las 10 gasolineras más baratas en orden ascendente.
            """
        )
