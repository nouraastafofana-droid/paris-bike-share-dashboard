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
def get_marker_color(num_bikes_available):
    if num_bikes_available > 5:
        return 'green'
    elif 0 < num_bikes_available <= 3:
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
