import streamlit as st
import requests
import re
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(page_title="Seaoil Fleet Intelligence", layout="wide")

# --- UI Styling ---
st.markdown("""
<style>
    .stTextInput > div > div > input { background-color: #f0f2f6; }
    .station-card {
        border: 2px solid #e6e9ef;
        padding: 20px;
        border-radius: 10px;
        background-color: white;
        margin-bottom: 20px;
        height: 100%;
    }
    .highway-badge {
        background-color: #1a73e8;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# --- Core Logic ---

def parse_google_url(url):
    """Extracts coordinates from Google Maps URLs including shortened links."""
    try:
        regex = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
        match = re.search(regex, url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # Resolve redirects for mobile/shortened links
        if "goo.gl" in url or "maps.app.goo.gl" in url:
            resolved_url = requests.get(url, allow_redirects=True).url
            match = re.search(regex, resolved_url)
            if match:
                return float(match.group(1)), float(match.group(2))
        return None
    except:
        return None

def get_seaoil_stations(coords):
    """
    Mimics a real Google Maps search using 'SEAOIL' as the primary keyword.
    Searches both local (5km) and highway-strategic (15km).
    """
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    
    # We use 'SEAOIL' in all-caps as the query, but the API is case-insensitive
    # This will find "SEAOIL", "Seaoil", and "seaoil"
    params = {
        "query": "SEAOIL gas station",
        "location": f"{coords[0]},{coords[1]}",
        "radius": 15000, # Max search radius
        "key": GOOGLE_API_KEY
    }
    
    response = requests.get(url, params=params).json()
    return response.get("results", [])

def get_street_view(lat, lng):
    return f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={lat},{lng}&key={GOOGLE_API_KEY}"

# --- App Interface ---

st.title("Fleet Intelligence Dashboard")
st.write("Enter a Google Maps URL to identify nearby and highway-accessible SEAOIL stations.")

url_input = st.text_input("Google Maps URL", placeholder="https://www.google.com/maps/place/...")

if st.button("Analyze Strategic Coverage") and url_input:
    client_coords = parse_google_url(url_input)
    
    if not client_coords:
        st.error("Could not find coordinates in that link. Please make sure the URL contains the '@lat,long' format.")
    else:
        with st.spinner("Scanning for SEAOIL stations..."):
            all_stations = get_seaoil_stations(client_coords)
            
            if not all_stations:
                st.warning("No SEAOIL stations found within 15km.")
            else:
                processed = []
                for s in all_stations:
                    s_coords = (s['geometry']['location']['lat'], s['geometry']['location']['lng'])
                    dist = geodesic(client_coords, s_coords).km
                    addr = s.get('formatted_address', '')
                    
                    # Logic: Is it on a major route?
                    # Checks for common PH highway markers
                    highway_keywords = ['Hwy', 'Highway', 'AH26', 'Expressway', 'SLEX', 'NLEX', 'Diversion', 'Circumferential']
                    is_hwy = any(key.lower() in addr.lower() for key in highway_keywords)
                    
                    # Scoring: 
                    # 1. Closer is better (up to 50 pts)
                    # 2. Highway access (30 pts)
                    # 3. High proximity (<2km) (20 pts)
                    score = 0
                    if dist <= 15: score += 10
                    if dist <= 5: score += 20
                    if dist <= 2: score += 20
                    if is_hwy: score += 50
                    
                    processed.append({
                        "name": s['name'],
                        "address": addr,
                        "dist": round(dist, 2),
                        "score": score,
                        "coords": s_coords,
                        "is_hwy": is_hwy
                    })

                # Sort: Best score first, then shortest distance
                ranked = sorted(processed, key=lambda x: (-x['score'], x['dist']))[:6]

                # --- Visuals ---
                m = folium.Map(location=client_coords, zoom_start=12)
                folium.Marker(client_coords, tooltip="CLIENT", icon=folium.Icon(color='red', icon='building', prefix='fa')).add_to(m)
                
                for s in ranked:
                    folium.Marker(
                        s['coords'],
                        tooltip=f"{s['name']}",
                        icon=folium.Icon(color='blue' if not s['is_hwy'] else 'orange', icon='gas-pump', prefix='fa')
                    ).add_to(m)

                st.subheader("Strategic Coverage Map")
                st_folium(m, width="100%", height=500)

                st.subheader("Top 6 Recommended SEAOIL Stations")
                
                grid = st.columns(2)
                for idx, s in enumerate(ranked):
                    with grid[idx % 2]:
                        hwy_label = '<span class="highway-badge">Major Route</span>' if s['is_hwy'] else ""
                        st.markdown(f"""
                        <div class="station-card">
                            <h3 style="margin-bottom:5px;">{s['name']}</h3>
                            {hwy_label}
                            <p style="color:#666; font-size:0.9em; margin-top:10px;">{s['address']}</p>
                            <p><b>Distance:</b> {s['dist']} km</p>
                            <p><b>Strategic Score:</b> {s['score']}/100</p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.image(get_street_view(*s['coords']))
