import streamlit as st
from helpers import *
import folium
import json
from streamlit_folium import st_folium

# -----------------------------
# Translations
# -----------------------------

TEXTS = {
    "fr": {
        "title": "Dashboard Vélib' Paris",
        "subtitle": "Explorez en temps réel la disponibilité des vélos et des stations Vélib' à Paris.",
        "bikes_available": "Vélos disponibles",
        "ebikes_available": "Vélos électriques disponibles",
        "station_available": "Stations avec vélos disponibles",
        "station_ebike_available": "Stations avec ≥ 5 e-bikes",
        "station_without_docks": "Stations sans bornettes disponibles",
        "filter": "Filtres",
        "user_need": "Que voulez-vous faire ?",
        "rent_bike": "Louer un vélo",
        "return_bike": "Déposer un vélo",
        "bike_type": "Type de vélo",
        "mechanical": "Mécanique",
        "electric": "Électrique",
        "location": "Où êtes-vous situé(e) ?",
        "street": "Adresse",
        "city": "Ville",
        "country": "Pays",
        "find_station": "Trouver une station",
        "drive": "Afficher l'itinéraire",
        "invalid_address": "Adresse introuvable. Essayez une adresse plus précise.",
        "ask_location": "Veuillez renseigner une adresse.",
        "map_available_bikes": "Vélos disponibles",
        "map_available_ebikes": "Vélos électriques disponibles",
        "map_available_mech": "Vélos mécaniques disponibles",
        "map_available_dock": "Bornettes disponibles",
        "here": "Vous êtes ici",
        "return_here": "Station recommandée",
        "duration_to": "Temps de trajet (min)",
        "loading_data": "Chargement des données Vélib'...",
        "loading_station": "Recherche de la station la plus proche...",
        "loading_route": "Calcul de l'itinéraire...",
    },
    "en": {
        "title": "Paris Bike Share Dashboard",
        "subtitle": "Explore real-time bike and station availability across Paris.",
        "bikes_available": "Bikes available",
        "ebikes_available": "E-Bikes available",
        "station_available": "Stations with available bikes",
        "station_ebike_available": "Stations with ≥ 5 e-bikes",
        "station_without_docks": "Stations without available docks",
        "filter": "Filters",
        "user_need": "What do you want to do?",
        "rent_bike": "Rent a bike",
        "return_bike": "Return a bike",
        "bike_type": "Bike type",
        "mechanical": "Mechanical",
        "electric": "Electric",
        "location": "Where are you located?",
        "street": "Street address",
        "city": "City",
        "country": "Country",
        "find_station": "Find a station",
        "drive": "Show route",
        "invalid_address": "Address not found. Try a more precise address.",
        "ask_location": "Please enter your location.",
        "map_available_bikes": "Available bikes",
        "map_available_ebikes": "E-Bikes available",
        "map_available_mech": "Mechanical bikes available",
        "map_available_dock": "Docks available",
        "here": "You are here",
        "return_here": "Recommended station",
        "duration_to": "Travel time (min)",
        "loading_data": "Loading Vélib' data...",
        "loading_station": "Finding nearest station...",
        "loading_route": "Calculating route...",
    },
}


# -----------------------------
# Data loading
# -----------------------------

STATUS_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"
INFO_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json"


@st.cache_data(ttl=120)
def load_data():
    df_status = get_station_status(STATUS_URL)
    df_info = get_station_information(INFO_URL)
    return join(df_status, df_info)


# -----------------------------
# Session state
# -----------------------------

if "iamhere" not in st.session_state:
    st.session_state.iamhere = None
if "search_done" not in st.session_state:
    st.session_state.search_done = False


# -----------------------------
# Map helpers
# -----------------------------

def make_popup_html(row, texts):
    return f"""
    <div style="width:300px; font-size:15px; line-height:1.6;">
        <b style="font-size:17px;">{row["name"]}</b><br><br>
        {texts["map_available_bikes"]}: <b>{row["num_bikes_available"]}</b><br>
        {texts["map_available_ebikes"]}: <b>{row["electric_bikes"]}</b><br>
        {texts["map_available_mech"]}: <b>{row["mechanical_bikes"]}</b><br>
        {texts["map_available_dock"]}: <b>{row["num_docks_available"]}</b>
    </div>"""


def add_station_layer(fmap, map_data, availability_col, texts):
    features = []
    for _, row in map_data.iterrows():
        color = get_marker_color(row[availability_col])
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["lon"], row["lat"]]
            },
            "properties": {
                "color": color,
                "popup": make_popup_html(row, texts),
            }
        })

    folium.GeoJson(
        {"type": "FeatureCollection", "features": features},
        marker=folium.CircleMarker(radius=4),
        style_function=lambda f: {
            "color":       f["properties"]["color"],
            "fillColor":   f["properties"]["color"],
            "fillOpacity": 0.7,
            "weight":      1,
        },
        popup=folium.GeoJsonPopup(fields=["popup"], labels=False),
    ).add_to(fmap)


# -----------------------------
# Sidebar controls
# -----------------------------

language = st.sidebar.selectbox("Language / Langue", ["Français", "English"])
lang = "fr" if language == "Français" else "en"
T = TEXTS[lang]

st.sidebar.divider()
st.sidebar.title(T["filter"])

user_need = st.sidebar.radio(T["user_need"], [T["rent_bike"], T["return_bike"]])

if "last_user_need" not in st.session_state:
    st.session_state.last_user_need = user_need
if st.session_state.last_user_need != user_need:
    st.session_state.search_done = False
    st.session_state.iamhere = None
    st.session_state.last_user_need = user_need

bike_type = []
show_route = False

if user_need == T["rent_bike"]:
    bike_type = st.sidebar.multiselect(
        T["bike_type"],
        [T["mechanical"], T["electric"]],
        default=[T["mechanical"], T["electric"]],
    )
    st.sidebar.subheader(T["location"])
    input_street = st.sidebar.text_input(T["street"], "")
    input_city = st.sidebar.text_input(T["city"], "Paris")
    input_country = st.sidebar.text_input(T["country"], "France")
    show_route = st.sidebar.checkbox(T["drive"], value=True)

    if st.sidebar.button(T["find_station"], type="primary"):
        if input_street.strip():
            with st.spinner(T["loading_station"]):
                coords = geocode(f"{input_street} {input_city} {input_country}")
            if coords is None:
                st.sidebar.error(T["invalid_address"])
            else:
                st.session_state.iamhere = coords
                st.session_state.search_done = True
        else:
            st.sidebar.error(T["ask_location"])

else:
    st.sidebar.subheader(T["location"])
    input_street = st.sidebar.text_input(T["street"], "")
    input_city = st.sidebar.text_input(T["city"], "Paris")
    input_country = st.sidebar.text_input(T["country"], "France")
    show_route = st.sidebar.checkbox(T["drive"], value=True)

    if st.sidebar.button(T["find_station"], type="primary"):
        if input_street.strip():
            with st.spinner(T["loading_station"]):
                coords = geocode(f"{input_street} {input_city} {input_country}")
            if coords is None:
                st.sidebar.error(T["invalid_address"])
            else:
                st.session_state.iamhere = coords
                st.session_state.search_done = True
        else:
            st.sidebar.error(T["ask_location"])


# -----------------------------
# Load data
# -----------------------------

with st.spinner(T["loading_data"]):
    data = load_data()

is_renting = user_need == T["rent_bike"]
availability_col = "num_bikes_available" if is_renting else "num_docks_available"
map_data = data[data[availability_col] > 0]


# -----------------------------
# Main page — KPIs
# -----------------------------

st.title(T["title"])
st.write(T["subtitle"])

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(T["bikes_available"], data["num_bikes_available"].sum())
    st.metric(T["ebikes_available"], data["electric_bikes"].sum())
with col2:
    st.metric(T["station_available"], (data["num_bikes_available"] > 0).sum())
    st.metric(T["station_ebike_available"], (data["electric_bikes"] >= 5).sum())
with col3:
    st.metric(T["station_without_docks"], (data["num_docks_available"] == 0).sum())


# -----------------------------
# Interactive map
# -----------------------------

iamhere = st.session_state.iamhere
search_done = st.session_state.search_done

if not search_done or iamhere is None:
    m = folium.Map(location=[48.866667, 2.333333], zoom_start=12, tiles="cartodbpositron")
    add_station_layer(m, map_data, availability_col, T)
    st_folium(m, width=900, height=600)

else:
    if is_renting:
        chosen_station = get_nearest_station_rent(iamhere, data, bike_type)
    else:
        chosen_station = get_nearest_station_return(iamhere, data)

    # Récupération de la ligne complète de la station
    station_row = data[data["station_id"] == chosen_station[0]].iloc[0]

    # Géocodage inversé de la station recommandée
    adresse = reverse_geocode((chosen_station[1], chosen_station[2]))

    popup_html = f"""
    <div style="width:300px; font-size:15px; line-height:1.6;">
        <b style="font-size:17px;">{T["return_here"]}</b><br>
        <i>{adresse}</i><br><br>
        {T["map_available_bikes"]}: <b>{station_row["num_bikes_available"]}</b><br>
        {T["map_available_ebikes"]}: <b>{station_row["electric_bikes"]}</b><br>
        {T["map_available_mech"]}: <b>{station_row["mechanical_bikes"]}</b><br>
        {T["map_available_dock"]}: <b>{station_row["num_docks_available"]}</b>
    </div>"""

    m = folium.Map(location=iamhere, zoom_start=16, tiles="cartodbpositron")
    add_station_layer(m, map_data, availability_col, T)

    folium.Marker(
        location=iamhere,
        popup=T["here"],
        icon=folium.Icon(color="blue", icon="person", prefix="fa"),
    ).add_to(m)

    folium.Marker(
        location=(chosen_station[1], chosen_station[2]),
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color="red", icon="bicycle", prefix="fa"),
    ).add_to(m)

    if show_route:
        with st.spinner(T["loading_route"]):
            coordinates, duration = run(chosen_station, iamhere)
        folium.PolyLine(
            locations=coordinates,
            color="blue",
            weight=5,
            tooltip=f"{duration} min",
        ).add_to(m)
        with col3:
            st.metric(T["duration_to"], f"{duration} min")

    st_folium(m, width=900, height=600)
