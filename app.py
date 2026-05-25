import streamlit as st
from helpers import *
import pandas as pd
import json
import requests
import folium  # Import folium for creating interactive maps
from streamlit_folium import folium_static
from streamlit_folium import st_folium

# -----------------------------
# Translations
# -----------------------------

TEXTS = {
    "fr": {
        "title": "Dashboard Vélib' Paris",
        "subtitle": "Explorez en temps réel la disponibilité des vélos et des stations Vélib' à Paris.",
        "raw_data": "Aperçu des données brutes",

        "bikes_available": "Vélos disponibles actuellement",
        "ebikes_available": "Vélos électriques disponibles",
        "station_available": "Stations avec vélos disponibles",
        "station_ebike_available": "Stations avec ≥ 5 e-bikes",
        "station_without_docks": "Stations sans bornettes disponibles",

        "filter": "Filtres",
        "user_need": "Que voulez-vous faire ?",
        "rent_bike": "Louer un vélo",
        "return_bike": "Déposer un vélo",
        "bike_type": "Type de vélo",
        "all_bikes": "Tous",
        "mechanical": "Mécanique",
        "electric": "Électrique",
        "station_search": "Rechercher une station",
        "location": "Où êtes-vous situé(e) ?",
        "street": "Adresse",
        "city": "Ville",
        "country": "Pays",
        "find_station": "Trouver une station",
        "drive": "J'y vais.",
        "invalid_address": "Adresse introuvable. Essayez une adresse plus précise",
        "ask_location": "Veuillez renseigner une adresse.",

        "map_available_bikes" : "Vélos disponibles",
        "map_available_ebikes" : "Vélos électriques disponibles",
        "map_available_mech" : "Vélos mécaniques disponibles",
        "map_available_dock" : "Bornettes disponibles",
    },
    "en": {
        "title": "Paris Bike Share Dashboard",
        "subtitle": "Explore real-time bike and station availability across Paris.",
        "raw_data": "Raw data preview",

        "bikes_available": "Bikes available now",
        "ebikes_available": "E-Bikes available now",
        "station_available": "Stations with available bikes",
        "station_ebike_available": "Stations with ≥ 5 e-bikes",
        "station_without_docks": "Stations without available docks",

        "filter": "Filters",
        "user_need": "What do you want to do?",
        "rent_bike": "Rent a bike",
        "return_bike": "Return a bike",
        "bike_type": "Bike type",
        "all_bikes": "All",
        "mechanical": "Mechanical",
        "electric": "Electric",
        "station_search": "Search a station",
        "location": "Where are you located?",
        "street": "Street address",
        "city": "City",
        "country": "Country",
        "find_station": "Find a station",
        "drive": "I'm driving there.",
        "invalid_address": "Input address not valid!",
        "ask_location": "Please input your location.",

        "map_available_bikes" : "Available bikes",
        "map_available_ebikes" : "e-Bikes available",
        "map_available_mech" : "mechanical bikes available",
        "map_available_dock" : "Docks available",
    }
}


# -----------------------------
# Sidebar controls
# -----------------------------



language = st.sidebar.selectbox(
    "Language / Langue",
    ["Français", "English"]
)

lang = "fr" if language == "Français" else "en"

st.sidebar.divider()

st.sidebar.title(TEXTS[lang]["filter"])

user_need = st.sidebar.radio(
    TEXTS[lang]["user_need"],
    [TEXTS[lang]["rent_bike"], TEXTS[lang]["return_bike"]]
)

# Initialisations
bike_type = None
iamhere = 0
iamhere_return = 0
search_button = False
search_button_dock = False

if user_need == TEXTS[lang]["rent_bike"]:
    bike_type = st.sidebar.multiselect(
            TEXTS[lang]["bike_type"],
            [
                TEXTS[lang]["mechanical"],
                TEXTS[lang]["electric"]
            ],
            default=[
                TEXTS[lang]["mechanical"],
                TEXTS[lang]["electric"]
            ]
        )

    st.sidebar.subheader(TEXTS[lang]["location"])
    input_street = st.sidebar.text_input(TEXTS[lang]["street"], "")
    input_city = st.sidebar.text_input(TEXTS[lang]["city"], "Paris")
    input_country = st.sidebar.text_input(TEXTS[lang]["country"], "France")

    drive = st.sidebar.checkbox(TEXTS[lang]["drive"])

    search_button = st.sidebar.button( TEXTS[lang]["find_station"], type="primary")
    if search_button:
        if input_street != "":
            iamhere = geocode( input_street + " " + input_city + " " + input_country)
            if iamhere == "":
                st.sidebar.error(TEXTS[lang]["invalid_address"])
        else:
            st.sidebar.error(TEXTS[lang]["ask_location"])


elif user_need == TEXTS[lang]["return_bike"]:
    st.sidebar.subheader(TEXTS[lang]["location"])
    input_street_return = st.sidebar.text_input(TEXTS[lang]["street"], "")
    input_city_return = st.sidebar.text_input(TEXTS[lang]["city"], "Paris")
    input_country_return = st.sidebar.text_input(TEXTS[lang]["country"], "France")

    search_button_dock = st.sidebar.button( TEXTS[lang]["find_station"], type="primary")
    if search_button_dock:
        if input_street_return != "":
            iamhere_return = geocode( input_street_return + " " + input_city_return + " " + input_country_return)
            if iamhere_return == "":
                st.sidebar.error(TEXTS[lang]["invalid_address"])
        else:
            st.sidebar.error(TEXTS[lang]["ask_location"])





# -----------------------------
# Data loading
# -----------------------------
STATUS_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
INFO_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json"

df_status = get_station_status(STATUS_URL)
df_info = get_station_information(INFO_URL)
data = join(df_status, df_info)


# -----------------------------
# Main page
# -----------------------------

st.title(TEXTS[lang]["title"])
st.write(TEXTS[lang]["subtitle"])

st.subheader(TEXTS[lang]["raw_data"])
st.dataframe(data.head())


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label = TEXTS[lang]["bikes_available"], value = data["num_bikes_available"].sum())
    st.metric(label = TEXTS[lang]["ebikes_available"], value = data["electric_bikes"].sum())

with col2:
    st.metric(label = TEXTS[lang]["station_available"], value = len(data[data['num_bikes_available'] > 0]))
    st.metric(label = TEXTS[lang]["station_ebike_available"], value = len(data[data['electric_bikes'] >= 5]))

with col3:
    st.metric(label = TEXTS[lang]["station_without_docks"], value = (data["num_docks_available"] == 0).sum())
# -----------------------------
# Interactive map
# -----------------------------

availability_column = (
    "num_bikes_available"
    if user_need in ["Louer un vélo", "Rent a bike"]
    else "num_docks_available"
)

if search_button_dock == False or search_button == False:
    center =[ 48.866667, 2.333333] #Coordonnées du centre de Paris
    m = folium.Map(location=center, zoom_start=12, tiles='cartodbpositron')

    for _, row in data.iterrows():
        marker_color = get_marker_color( row[availability_column])
        popup_html = f"""
        <div style="width: 260px;">
        <b>{row["name"]}</b><br><br>

        {TEXTS[lang]["map_available_bikes"]}:
        <b>{row["num_bikes_available"]}</b><br>

        {TEXTS[lang]["map_available_ebikes"]}:
        <b>{row["electric_bikes"]}</b><br>

        {TEXTS[lang]["map_available_mech"]}:
        <b>{row["mechanical_bikes"]}</b><br>

        {TEXTS[lang]["map_available_dock"]}:
        <b>{row["num_docks_available"]}</b>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=4,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row["name"]
        ).add_to(m)

    st_folium(m, width=900, height=600)
