import streamlit as st
import requests
import re  # Added for URL parsing
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(
    page_title="Seaoil Fleet Intelligence Dashboard",
    layout="wide"
)

# --- UI Header & Logo ---
# Using the Seaoil logo from a public URL
col1, col2, col3 = st.columns([2, 1, 2])
with col2:
    st.image("https://www.seaoil.com.ph/assets/img/seaoil-logo.png", width=200)

st.markdown("<h1 style='text-align: center;'>Fleet Intelligence Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Strategic Station Mapping Tool</p>", unsafe_allow_html=True)

# --- Helper Functions ---

def parse_google_url(url):
    """Extracts (lat, lng) from a Google Maps URL."""
    try:
        # Regex to find patterns like @14.5833,121.0544
        regex = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
        match = re.search(regex, url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # If the URL is a shortened 'goo.gl' link, we need to resolve it first
        if "goo.gl" in url or "maps.app.goo.gl" in url:
            resolved_url = requests.get(url, allow_redirects=True).url
            match = re.search(regex, resolved_url)
            if match:
                return float(match.group(1)), float(match.group(2))
        
        return None
    except Exception:
        return None

def find_seaoil_stations(client_coords):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{client_coords[0]},{client_coords[1]}",
        "radius": 5000,
        "keyword": "Seaoil",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params).json()
    return response.get("results", [])

def check_highway_proximity(station_coords):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{station_coords[0]},{station_coords[1]}",
        "radius": 1200,
        "keyword": "highway",
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params).json()
    return len(response.get("results", [])) > 0

def get_street_view_image(lat, lng):
    return f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={lat},{lng}&key={GOOGLE_API_KEY}"

# --- User Input ---
map_url = st.text_input("Paste Google Maps URL", placeholder="https://www.google.com/maps/place/...")

if st.button("Analyze Strategic Coverage") and map_url:
    client_coords = parse_google_url(map_url)
    
    if not client_coords:
        st.error("Could not extract coordinates from that link. Please use a full Google Maps URL containing '@latitude,longitude'.")
    else:
        stations = find_seaoil_stations(client_coords)

        if not stations:
            st.warning("No Seaoil stations found within 5km of this location.")
        else:
            ranked = []
            for station in stations:
                s_lat = station['geometry']['location']['lat']
                s_lng = station['geometry']['location']['lng']
                station_coords = (s_lat, s_lng)

                dist = geodesic(client_coords, station_coords).km
                is_hwy = check_highway_proximity(station_coords)

                score = 0
                if dist <= 2: score += 50
                if is_hwy: score += 50

                ranked.append({
                    "name": station["name"],
                    "coords": station_coords,
                    "distance": round(dist, 2),
                    "highway": is_hwy,
                    "score": score
                })

            ranked = sorted(ranked, key=lambda x: x["score"], reverse=True)[:6]

            # --- Display Map ---
            st.subheader("Strategic Coverage Map")
            m = folium.Map(location=client_coords, zoom_start=14)
            folium.Marker(client_coords, tooltip="Client Location", icon=folium.Icon(color='red', icon='briefcase')).add_to(m)

            for station in ranked:
                folium.Marker(
                    station["coords"],
                    tooltip=f"{station['name']} | Score: {station['score']}",
                    icon=folium.Icon(color='blue', icon='fuel')
                ).add_to(m)

            st_folium(m, width="100%", height=500)

            # --- Display Cards ---
            st.subheader("Top 6 Strategic Stations")
            cols = st.columns(2) # Display cards in two columns
            for i, station in enumerate(ranked):
                with cols[i % 2]:
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
                        <h4 style="color: #ed1c24;">{station['name']}</h4>
                        <b>Distance:</b> {station['distance']} km<br>
                        <b>Highway Access:</b> {"✅ Yes" if station["highway"] else "❌ No"}<br>
                        <b>Rank Score:</b> {station['score']}/100
                    </div>
                    """, unsafe_allow_html=True)
                    st.image(get_street_view_image(*station["coords"]))
