# Vélib' Paris — Real-Time Dashboard

An interactive data application for visualizing and navigating the Vélib' Métropole bike-share network across Paris, built with Python and Streamlit.

---

## Overview

The app queries the Vélib' Métropole open data API in real time and helps users instantly locate the nearest available station whether they need to rent or return a bike, along with a live route and estimated travel time.

---

## Features

- **Interactive map** of all Parisian stations with color-coded availability (green / yellow / red)
- **Address-based geolocation** : the user inputs their address and the app identifies the optimal station
- **Bike type filter** : mechanical, electric, or both
- **Two modes** : find an available bike, or find a free dock to return one
- **Live routing** via the OSRM API with travel time estimation
- **Enriched popup** on the recommended station : exact address, detailed availability
- **Bilingual interface** French / English

---

## Tech Stack

| Layer                  | Technology                     |
| ---------------------- | ------------------------------ |
| Interface              | Streamlit                      |
| Mapping                | Folium + streamlit-folium      |
| Data source            | Vélib' Métropole Open Data API |
| Geocoding              | Geopy                          |
| Routing                | OSRM API                       |
| Vectorized computation | NumPy (Haversine formula)      |
| Data processing        | Pandas                         |

---

## Technical Highlights

- **Map rendering optimization** : all stations rendered as a single GeoJSON layer instead of ~1,400 individual CircleMarker objects, significantly reducing browser load
- **Vectorized distance computation** : Haversine formula implemented with NumPy array operations instead of sequential geodesic calls
- **Multi-level caching strategy** : Vélib' data (`ttl=120s`) and geocoding results (`ttl=24h`) cached via `@st.cache_data` to minimize redundant API calls

---

## Getting Started

```bash
git clone https://github.com/ton-user/paris-bike-share-dashboard.git
cd paris-bike-share-dashboard
pip install -r requirements.txt
streamlit run app.py
```

---

## Data Sources

- [Vélib' Métropole Open Data](https://www.velib-metropole.fr/donnees-open-data-gbfs-du-service-velib-metropole) — real-time feed
- [OSRM](http://project-osrm.org/) — open-source routing engine
- [Nominatim / OpenStreetMap](https://nominatim.org/) — geocoding
