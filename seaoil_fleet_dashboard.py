import streamlit as st
import requests
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(
    page_title="Seaoil Fleet Intelligence Dashboard",
    layout="wide"
)

# ... (Your CSS remains the same) ...

st.title("Seaoil Fleet Intelligence Dashboard")
st.caption("Strategic Station Mapping Tool")

def geocode_address(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_API_KEY}
    try:
        response = requests.get(url, params=params).json()
        # CHECK: Does the results list actually have data?
        if response.get('results'):
            location = response['results'][0]['geometry']['location']
            return (location['lat'], location['lng'])
        else:
            return None
    except Exception as e:
        return None

def find_seaoil_stations(client_coords):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{client_coords[0]},{client_coords[1]}",
        "radius": 5000, # Increased radius slightly to ensure results
        "keyword": "Seaoil",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params).json()
    return response.get("results", [])

# ... (check_highway_proximity and get_street_view_image functions remain the same) ...

address = st.text_input("Client Business Address", placeholder="e.g. 123 Shaw Blvd, Mandaluyong")

if st.button("Analyze Strategic Coverage") and address:

    client_coords = geocode_address(address)
    
    # CHECK: Did geocoding succeed?
    if client_coords is None:
        st.error("Could not find that address. Please be more specific (e.g., include city or zip code).")
    else:
        stations = find_seaoil_stations(client_coords)

        if not stations:
            st.warning("No Seaoil stations found within the search radius of this address.")
        else:
            ranked = []
            for station in stations:
                station_coords = (
                    station['geometry']['location']['lat'],
                    station['geometry']['location']['lng']
                )

                distance = geodesic(client_coords, station_coords).km
                highway_near = check_highway_proximity(station_coords)

                score = 0
                if distance <= 2: score += 50
                if highway_near: score += 50

                ranked.append({
                    "name": station["name"],
                    "coords": station_coords,
                    "distance": round(distance, 2),
                    "highway": highway_near,
                    "score": score
                })

            ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)[:6]

            # Map rendering
            m = folium.Map(location=client_coords, zoom_start=13)
            folium.Marker(client_coords, tooltip="Client Location", icon=folium.Icon(color='red')).add_to(m)

            for station in ranked:
                folium.Marker(
                    station["coords"],
                    tooltip=f"{station['name']} | Score: {station['score']}"
                ).add_to(m)

            st.subheader("Strategic Coverage Map")
            st_folium(m, width=1000, height=500)

            st.subheader("Top Strategic Stations")
            for station in ranked:
                st.markdown(f"""
                <div class="result-card">
                <h4>{station['name']}</h4>
                <b>Distance from Client:</b> {station['distance']} km<br>
                <b>Near Highway:</b> {"Yes" if station["highway"] else "No"}<br>
                <b>Strategic Score:</b> {station['score']}/100
                </div>
                """, unsafe_allow_True=True)
                st.image(get_street_view_image(*station["coords"]))
