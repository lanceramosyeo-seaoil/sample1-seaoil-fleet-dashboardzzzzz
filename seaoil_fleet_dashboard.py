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

st.markdown("""
<style>
.main {
    background-color: #ffffff;
}
h1 {
    font-size: 32px;
    font-weight: 600;
}
.result-card {
    padding: 15px;
    border: 1px solid #e6e6e6;
    border-radius: 8px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

st.title("Seaoil Fleet Intelligence Dashboard")
st.caption("Strategic Station Mapping Tool")

def geocode_address(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_API_KEY}
    response = requests.get(url, params=params).json()
    location = response['results'][0]['geometry']['location']
    return (location['lat'], location['lng'])

def find_seaoil_stations(client_coords):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{client_coords[0]},{client_coords[1]}",
        "radius": 2000,
        "keyword": "Seaoil",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params).json()
    return response.get("results", [])

def check_highway_proximity(station_coords):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{station_coords[0]},{station_coords[1]}",
        "radius": 12000,
        "keyword": "highway",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params).json()
    return len(response.get("results", [])) > 0

def get_street_view_image(lat, lng):
    return f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={lat},{lng}&key={GOOGLE_API_KEY}"

address = st.text_input("Client Business Address")

if st.button("Analyze Strategic Coverage") and address:

    client_coords = geocode_address(address)
    stations = find_seaoil_stations(client_coords)

    ranked = []

    for station in stations:
        station_coords = (
            station['geometry']['location']['lat'],
            station['geometry']['location']['lng']
        )

        distance = geodesic(client_coords, station_coords).km
        highway_near = check_highway_proximity(station_coords)

        score = 0
        if distance <= 2:
            score += 50
        if highway_near:
            score += 50

        ranked.append({
            "name": station["name"],
            "coords": station_coords,
            "distance": round(distance,2),
            "highway": highway_near,
            "score": score
        })

    ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)[:6]

    m = folium.Map(location=client_coords, zoom_start=13)

    folium.Marker(client_coords, tooltip="Client Location").add_to(m)

    for station in ranked:
        folium.Marker(
            station["coords"],
            tooltip=f"{station['name']} | Score: {station['score']}"
        ).add_to(m)

    st.subheader("Strategic Coverage Map")
    st_folium(m, width=1000, height=500)

    st.subheader("Top 6 Strategic Stations")

    for station in ranked:
        st.markdown(f"""
        <div class="result-card">
        <h4>{station['name']}</h4>
        <b>Distance from Client:</b> {station['distance']} km<br>
        <b>Near Highway:</b> {"Yes" if station["highway"] else "No"}<br>
        <b>Strategic Score:</b> {station['score']}/100
        </div>
        """, unsafe_allow_html=True)

        st.image(get_street_view_image(*station["coords"]))
