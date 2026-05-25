import requests
import pandas as pd
import datetime as dt
import numpy as np
from geopy.geocoders import Nominatim
import folium
import streamlit as st


# -----------------------------
# Data fetching
# -----------------------------

def get_station_status(url):
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data["data"]["stations"])

    df = df[
        (df["is_installed"] == 1) &
        (df["is_renting"] == 1) &
        (df["is_returning"] == 1)
    ].drop_duplicates(["station_id", "last_reported"])

    df["last_reported"] = pd.to_datetime(df["last_reported"], unit="s")

    df["mechanical_bikes"] = df["num_bikes_available_types"].apply(
        lambda x: x[0].get("mechanical", 0)
    )
    df["electric_bikes"] = df["num_bikes_available_types"].apply(
        lambda x: x[1].get("ebike", 0)
    )
    return df


def get_station_information(url):
    response = requests.get(url)
    data = response.json()
    return pd.DataFrame(data["data"]["stations"])


def join(df_status, df_info):
    return df_status.merge(
        df_info[["station_id", "name", "lat", "lon", "capacity", "rental_methods"]],
        how="left",
        on="station_id",
    )


# -----------------------------
# Map helpers
# -----------------------------

def get_marker_color(availability):
    if availability > 5:
        return "green"
    elif availability > 0:
        return "yellow"
    return "red"


# -----------------------------
# Geocoding
# TTL 24h : une adresse ne change pas dans la journée
# -----------------------------

@st.cache_data(ttl=86400)
def geocode(address):
    geolocator = Nominatim(user_agent="paris-bike-share-dashboard/1.0")
    location = geolocator.geocode(address)
    return (location.latitude, location.longitude) if location else None


@st.cache_data(ttl=86400)
def reverse_geocode(latlon):
    geolocator = Nominatim(user_agent="paris-bike-share-dashboard/1.0")
    location = geolocator.reverse(latlon)
    return location.address if location else None


# -----------------------------
# Distance computation
# -----------------------------

def _compute_distances(latlon, df):
    R = 6371
    lat1 = np.radians(latlon[0])
    lon1 = np.radians(latlon[1])
    lat2 = np.radians(df["lat"].values)
    lon2 = np.radians(df["lon"].values)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


# -----------------------------
# Station finders
# -----------------------------

def get_nearest_station_rent(latlon, df, bike_type):
    filtered = df.copy()

    if not bike_type or len(bike_type) == 2:
        filtered = filtered[
            (filtered["electric_bikes"] > 0) | (filtered["mechanical_bikes"] > 0)
        ]
    elif any(b in bike_type for b in ["Électrique", "Electric"]):
        filtered = filtered[filtered["electric_bikes"] > 0]
    elif any(b in bike_type for b in ["Mécanique", "Mechanical"]):
        filtered = filtered[filtered["mechanical_bikes"] > 0]

    filtered = filtered.reset_index(drop=True)
    filtered["distance"] = _compute_distances(latlon, filtered)

    nearest = filtered.loc[filtered["distance"].idxmin()]
    return [nearest["station_id"], nearest["lat"], nearest["lon"]]


def get_nearest_station_return(latlon, df):
    filtered = df[df["num_docks_available"] > 0].copy().reset_index(drop=True)
    filtered["distance"] = _compute_distances(latlon, filtered)

    nearest = filtered.loc[filtered["distance"].idxmin()]
    return [nearest["station_id"], nearest["lat"], nearest["lon"]]


# -----------------------------
# Routing
# -----------------------------

def run(chosen_station, iamhere):
    start = f"{iamhere[1]},{iamhere[0]}"
    end = f"{chosen_station[2]},{chosen_station[1]}"
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{start};{end}?geometries=geojson"
    )

    r = requests.get(url, headers={"Content-type": "application/json"})
    route = r.json()["routes"][0]

    coordinates = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
    duration = round(route["duration"] / 60, 1)

    return coordinates, duration
