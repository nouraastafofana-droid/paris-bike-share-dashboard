import requests
import pandas as pd
import datetime as dt
from geopy.distance import geodesic  # Import geodesic for calculating distances
from geopy.geocoders import Nominatim  # Import Nominatim for geocoding
import folium  # Import folium for creating interactive maps

def get_station_status(url):

    response = requests.get(url)
    data = response.json()
    stations = data["data"]["stations"]
    df = pd.DataFrame(stations)

    df = df[df["is_installed"] == 1] #Keep only stationsthat are deployed
    df = df[df["is_renting"] == 1] #Keep only stations that are renting
    df = df[df["is_returning"] == 1] #Keep only stations accepting bike returns

    df = df.drop_duplicates(["station_id", "last_reported"]) # Remove duplicate station reports

    df["last_reported"] = df["last_reported"].apply(lambda x: dt.datetime.fromtimestamp(x)) # Convert Unix timestamp to datetime

    #df['time'] = data['lastUpdatedOther']  # Add the last updated time to the DataFrame
    #df.time = df.time.map(lambda x: dt.datetime.utcfromtimestamp(x))  # Convert timestamps to datetime
    #df = df.set_index('time')  # Set the time as the index
    #df.index = df.index.tz_localize('UTC')  # Localize the index to UTC

    # Extract mechanical and electric bike counts into separate columns
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
    stations = data["data"]["stations"]

    df = pd.DataFrame(stations)

    return df


def join(df1, df2):
    df = df1.merge(df2[['station_id', 'name', 'lat', 'lon', 'capacity', 'rental_methods']],
                how='left',
                on='station_id')
    return df


# Function to determine marker color based on the number of bikes available
def get_marker_color(availability):
    if availability > 5:
        return 'green'
    elif 0 < availability <= 5:
        return 'yellow'
    else:
        return 'red'


# Define the function to geocode an address
def geocode(address):
    geolocator = Nominatim(user_agent="paris-bike-share-dashboard/1.0")  # Create a geolocator object
    location = geolocator.geocode(address)  # Geocode the address
    if location is None:
        return None  # Return an empty string if the address is not found
    else:
        return (location.latitude, location.longitude)  # Return the latitude and longitude


def get_nearest_station_rent(latlon, df, input_bike_modes):
    filtered_df = df.copy()
    if len(bike_type) == 0 or len(bike_type) == 2:
        filtered_df = filtered_df[ (filtered_df["electric_bikes"] > 0) | (filtered_df["mechanical_bikes"] > 0)]

    elif bike_modes[0] in ["Électrique", "Electric"]:
        filtered_df = filtered_df[ filtered_df["electric_bikes"] > 0]

    elif bike_modes[0] in ["Mécanique", "Mechanical"]:
        filtered_df = filtered_df[ filtered_df["mechanical_bikes"] > 0]

    i = 0
    filtered_df["distance"] = ""
    while i < len(filtered_df):
        filtered_df.loc[i, "distance"] = geodesic(latlon, (filtered_df["lat"][i], filtered_df["lon"][i] )).km
        i = i + 1

    chosen_station = []
    chosen_station.append(filtered_df[filtered_df["distance"] == min(filtered_df["distance"])]["station_id"].iloc[0])
    chosen_station.append(filtered_df[filtered_df["distance"] == min(filtered_df["distance"])]["lat"].iloc[0])
    chosen_station.append(filtered_df[filtered_df["distance"] == min(filtered_df["distance"])]["lon"].iloc[0])

    return chosen_station


def get_nearest_station_return(latlon, df):
    filtered_df = df.copy()
    filtered_df = filtered_df[ filtered_df["num_docks_available"] > 0]

    i = 0
    filtered_df["distance"] = ""
    while i < len(filtered_df):
        filtered_df.loc[i, "distance"] = geodesic(latlon, (filtered_df["lat"][i], filtered_df["lon"][i] )).km
        i = i + 1

    chosen_station = []
    chosen_station.append(filtered_df[filtered_df["distance"] == min(filtered_df["distance"])]["station_id"].iloc[0])
    chosen_station.append(filtered_df[filtered_df["distance"] == min(filtered_df["distance"])]["lat"].iloc[0])
    chosen_station.append(filtered_df[filtered_df["distance"] == min(filtered_df["distance"])]["lon"].iloc[0])

    return chosen_station
