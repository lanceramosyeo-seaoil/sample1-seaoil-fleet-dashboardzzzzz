import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

# --- CONFIG & SECRETS ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

st.set_page_config(page_title="Seaoil Fleet Dashboard", layout="wide")

# Persistent State Fix
if 'data' not in st.session_state:
    st.session_state.data = None

# --- YOUR VERIFIED STATION LIST ---
RAW_BRANCHES = [
    "MERVILLE - PARANAQUE", "CALAUAN - LAGUNA", "55 C VIRA LAOAG - ILOCOS NORTE", "A BONI - QC",
    "AGUITAP SOLSONA - ILOCOS NORTE", "TANAYTAY ALAMINOS - PANGASINAN", "ALAMINOS - LAGUNA",
    "ANAYAN PILI - CAMARINES SUR", "ARENAS ARAYAT - PAMPANGA", "AYALA HIGHWAY - LIPABACARRA",
    "STA. BALBINA - LAOAG", "BAGONG KALSADA - LAGUNA", "BAGONG POOK STA MARIA - LAGUNA",
    "BAKIR BAGABAG - NUEVA VIZCAYA", "BALIWAG - BULACAN", "SAN JOSE - BARAS", "BINAN - LAGUNA",
    "BONIFACIO AVE - CAINTA", "C5 UGONG - PASIG CITY", "CABALANGGAN BANTAY - ILOCOS SUR",
    "CABUAAN BALAOAN - LA UNION", "CADLAN PILI - CAMARINES SUR", "CAGAYAN VALLEY RD TABANG - PUTING BATO - BATANGAS",
    "CALAOCAN BAMBANG - NUEVA VIZCAYA", "CALIHAN SAN PABLO - LAGUNA", "CAMASI PENABLANCA - CAGAYAN",
    "PALIMBO-CAAROSIPAN - TARLAC", "CATBANGEN SAN FERNANDO - LA UNION", "CAWIT TAAL - BATANGAS",
    "CAYANGA SAN FABIAN - PANGASINAN", "CENTRO CABAGAN - ISABELA", "CUTCUT ANGELES - PAMPANGA",
    "DAMORTIS STO. TOMAS - LA UNION", "DEL MONTE - QC", "DISTRICT 3 SAN MANUEL - ISABELA",
    "GUMACA - QUEZON", "HARING CANAMAN - CAM SUR", "HIGHWAY 2000 SAN JUAN TAYTAY - RIZAL",
    "IMELDA SAMAL - BATAAN", "LALAAN - SILANG", "LIBAG SUR - TUGUEGARAO CITY", 
    "LINGALING TUMAUINI - ISABELA", "LIPA - BATANGAS", "LUMBANGAN NASUGBU - BATANGAS",
    "MABINI ST CATBANGEN - LA UNION", "MAITIM BAY - LAGUNA", "MAKILING CALAMBA - LAGUNA",
    "MANIBAUG - PORAC", "MARAYKIT SAN JUAN - BATANGAS", "MARIA CLARA DIFFUN - QUIRINO",
    "MAYAPA - LAGUNA", "POBLACION 7 MENDEZ - CAVITE", "MONTALBAN - RIZAL", "MORONG - RIZAL",
    "NANGALISAN EAST - LAOAG", "NATL HIWAY STA LUCIA - ILOCOS SUR", "NORZAGARAY - BULACAN",
    "PALLOCAN EAST - BATANGAS CITY", "PANDAN ANGELES - PAMPANGA", "PANIKIHAN GUMACA - QUEZON",
    "PARALUMAN - MARIKINA", "PEDRO GIL BRGY 685 PACO - MANILA", "PEREZ BLVD SAN CARLOS - PANGASINAN",
    "PUTING KAHOY SILANG - CAVITE", "ROSARIO - LA UNION", "SAN AQUILINO - ROXAS",
    "SAN FRANCISCO BINAN - LAGUNA", "SAN FRANCISCO - MABALACAT CITY", "SAN ISIDRO SUCAT - PARANAQUE",
    "SAN JUAN - BATANGAS", "SAN JUAN TAYTAY - RIZAL", "SAN MARTIN DE PORRES - PARANAQUE CITY",
    "MAHARLIKA CAMIAS - BULACAN", "MAHARLIKA SAN ROQUE - LAGUNA", "SAN PABLO STO DOMINGO - ILOCOS",
    "SAN VICENTE II SILANG - CAVITE", "SAN VICENTE SANTA CRUZ - OCC MINDORO", "SANTIAGO - BARAS",
    "SCTEX SANTIAGO - TARLAC", "SINDALAN - SAN FERNANDO", "SINILOAN - LAGUNA", 
    "ROXAS SOLANO - NUEVA VIZCAYA", "STA RITA GUADALUPE NUEVO - MAKATI CITY",
    "STO DOMINGO ANGELES - PAMPANGA", "POB 1 STO TOMAS - BATANGAS", "SUCAT - PARANAQUE",
    "TABON III KAWIT - CAVITE", "TABUCO NAGA - CAMARINES SUR", "TAMBO PAMPLONA - CAMARINES SUR",
    "TORAN APARRI - CAGAYANTUNASAN - MUNTINLUPA", "TUROD SUR CORDON - ISABELA", 
    "VELASQUEZ BANGIAD TAYTAY - RIZAL", "JP RIZAL - MARIKINA", "LDO ARWAS - BANILDO BACOLOR - PAMPANGA",
    "LDO BANAG - ALBAY", "LDO BASCARAN DARAGA - ALBAY", "LDO BATAL SANTIAGO - ISABELA",
    "LDO CABALANTIAN - PAMPANGA", "CABATACAN WEST LASAM - CAGAYAN", "CUTCUT GUIGUINTO - BULACAN",
    "LDO JOSE ABAD SANTOS TONDO - MANILA", "JP RIZAL AVE OLYMPIA - MAKATI", "LDO KARUHATAN - VALENZUELA",
    "LDO KAYPIAN SJDM - BULACAN", "LDO LAS PINAS - MANILA", "LDO LAWANG BATO - VALENZUELA",
    "NATL ROAD DAMPOL 1ST - PULILAN", "LDO SAN AGUSTIN CANDON - ILOCOS SUR", 
    "LDO SAN ISIDRO PILI - CAMARINES SUR", "LDO SAN RAFAEL MEXICO - PAMPANGA",
    "SAN RAMON DINALUPIHAN - BATAAN", "SEVILLA SAN FERNANDO - LA UNION", "LDO TELABASTAGAN - PAMPANGA",
    "BALAGTAS PARANG - MARIKINA", "MUZON - BATANGAS", "BAYACAT ST. SABUTAN - CAVITE",
    "AGONCILLO - BATANGAS", "MAGALANG - PAMPANGA", "A MABINI - CALOOCAN", "AMAYA - CAVITE",
    "ALIBAGU ILAGAN - ISABELA", "ANABU IMUS - CAVITE", "BULUANG BAAO - CAMARINES SUR",
    "ROMAN VILLA LUNA BALANGA - BATAAN", "BALATAS NAGA CITY - CAMARINES SUR", 
    "BANGA I PLARIDEL - BULACAN", "BAUAN - BATANGAS", "BETTY GO BEL MONTE - QC", 
    "BOCAUE - BULACAN", "BONGA BACACAY - ALBAY", "BRGY 177 CAMARIN - CALOOCAN",
    "BRGY 8 MAMBURAO - OCC MINDORO", "BUBUKAL - LAGUNA", "TANZANG LUMA III - CAVITE",
    "C5 COR ATIS UGONG - PASIG", "CAINTA - RIZAL", "CALAPAN BAYANAN - MINDORO", 
    "SAN MIGUEL - CALASIAO", "CAMINAWIT SAN JOSE - OCC MINDORO", "MANGILAG SUR - CANDELARIA",
    "CANLUBANG - LAGUNA", "MAHARLIKA CAPIHAN - BULACAN", "BANCAL CARMONA - CAVITE",
    "CENTRAL EAST 2 BANGAR - LA UNION", "COMMONWEALTH - QC", "CUASAY - TAGUIG", 
    "DILI BAUANG - LA UNION", "DIVERSION DOMOIT - QUEZON", "DONA JOSEFA - QC", 
    "E ROD - QC", "GEN LUIS - QC", "KATIPUNAN - MARIKINA", "LABANGAN SAN JOSE - OCC MINDORO",
    "LEGARDA - MANILA", "LOS BANOS - LAGUNA", "LUCENA - QUEZON", "LUMANGBAYAN ABRA DE ILOG - OCC MINDORO",
    "MABALACAT MAGALANG - PAMPANGA", "MAGASPAC GERONA - TARLAC", "MALITBOG BONGABONG - ORIENTAL MINDORO",
    "MALIWALO TARLAC CITY - TARLAC", "MALVAR - BATANGAS", "MARFRANCISCO PINAMALAYAN - MINDORO",
    "MAYBUNGA - PASIG", "MAYSAN - VALENZUELA", "MCARTHUR - MALOLOS", "NAMUNGA - BATANGAS",
    "NANGKA - MARIKINA", "NORTHBAY - MANILA", "SALCEDO 1 NOVELETA - CAVITE", "P TUAZON - QC",
    "PACO - MANILA", "PALATIW - PASIG", "PAMORANGON DAET - CAMARINES NORTE", "PANADEROS - MANILA",
    "PAOMBONG - BULACAN", "PARTIDA I GUIMBA - NUEVA ECIJA", "PASONG BUAYA II IMUS - CAVITE",
    "PASONG TAMO - QC", "HULO PILILIA - RIZAL", "PLAINVIEW - MANDALUYONG", 
    "POB EAST SANTA IGNACIA - TARLAC", "POLANGUI - ALBAY", "PRITIL - MANILA", 
    "RIZAL SANTIAGO CITY - ISABELA", "SABANG NAIC - CAVITE", "SALAWAG - CAVITE", 
    "SAN ANDRES - MANILA", "SAN ANTONIO - PASIG", "SAN ISIDRO ANGONO - RIZAL", 
    "TUNGKONG MANGGA - BULACAN", "SAN JOSE BULAKAN - BULACAN", "SAN MIGUEL - TAGUIG CITY",
    "SANTIAGO GEN TRIAS - CAVITE", "SHAW BLVD - MANDALUYONG CITY", "SINIPIT BONGABON - NUEVA ECIJA",
    "ST DOMINIC - QC", "STA CRUZ - MANILA", "STA ROSA - LAGUNA", "STO NINO SABLAYAN - OCC MINDORO",
    "SUMULONG HIWAY MAMBUGAN - ANTIPOLO", "LIBTONG - ILOCOS SUR", "TALABA CAINTA - RIZAL",
    "SAMPALOC LUBIGAN - RIZAL", "TANDANG SORA - QC", "TEJEROS - GENERAL TRIAS", 
    "TRECE MARTIRES INDANG RD - CAVITE", "USUSAN - TAGUIG", "ZONE III DASMARINAS - CAVITE",
    "PALIGUI APALIT - PAMPANGA", "EDSA - QC", "DAGAT DAGATAN - CALOOCAN"
]

# --- CORE LOGIC ---

def get_coords_from_url(url):
    """Parses Google Maps URL and resolves short-links to get @lat,long."""
    regex = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
    try:
        # Check if the URL already has the coords
        match = re.search(regex, url)
        if match:
            return float(match.group(1)), float(match.group(2))
        
        # If not, it might be a goo.gl or internal link, resolve it
        resolved = requests.get(url, allow_redirects=True, timeout=5).url
        match = re.search(regex, resolved)
        if match:
            return float(match.group(1)), float(match.group(2))
    except:
        return None
    return None

def get_driving_matrix(origin, destinations):
    """Fetches real travel time and distance."""
    dests = "|".join([f"{d['lat']},{d['lng']}" for d in destinations])
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin[0]},{origin[1]}&destinations={dests}&key={GOOGLE_API_KEY}"
    try:
        data = requests.get(url).json()
        return data['rows'][0]['elements']
    except:
        return [{"distance": {"text": "N/A"}, "duration": {"text": "N/A"}}] * len(destinations)

def find_seaoil_stations(coords):
    """Uses Text Search for SEAOIL and cross-references with your provided list."""
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=SEAOIL&location={coords[0]},{coords[1]}&radius=15000&key={GOOGLE_API_KEY}"
    results = requests.get(url).json().get("results", [])
    
    stations = []
    for r in results:
        name_upper = r['name'].upper()
        lat, lng = r['geometry']['location']['lat'], r['geometry']['location']['lng']
        
        # Scoring: Bonus if it matches a keyword from your list
        is_verified = any(word.split(" - ")[0] in name_upper for word in RAW_BRANCHES)
        
        # Format name to your requirement: SEAOIL - [BRANCH]
        clean_name = r['name'].replace("Seaoil", "").replace("SEAOIL", "").replace("-", "").strip()
        display_name = f"SEAOIL - {clean_name}"
        
        stations.append({
            "name": display_name,
            "address": r.get('formatted_address', 'N/A'),
            "lat": lat, "lng": lng,
            "is_verified": is_verified,
            "air_dist": round(geodesic(coords, (lat, lng)).km, 2)
        })
    
    # Take top 6 closest
    top_6 = sorted(stations, key=lambda x: (-x['is_verified'], x['air_dist']))[:6]
    
    # Add Distance Matrix Data
    matrix = get_driving_matrix(coords, top_6)
    for i, m in enumerate(matrix):
        top_6[i]['road_dist'] = m.get('distance', {}).get('text', 'N/A')
        top_6[i]['duration'] = m.get('duration', {}).get('text', 'N/A')
        
    return top_6

# --- USER INTERFACE ---

st.title("Seaoil Fleet Intelligence Dashboard")
st.subheader("📍 Strategic Proximity & Route Analysis")

url_input = st.text_input("Paste Google Maps Link (Client Location)", placeholder="https://maps.app.goo.gl/...")

if st.button("Analyze Fleet Proximity"):
    with st.spinner("Decoding URL and searching for stations..."):
        coords = get_coords_from_url(url_input)
        if coords:
            stations = find_seaoil_stations(coords)
            st.session_state.data = {"coords": coords, "stations": stations}
        else:
            st.error("Could not find coordinates in that link. Please use a standard Google Maps share link.")

# PERSISTENT RESULTS DISPLAY
if st.session_state.data:
    d = st.session_state.data
    
    # 1. Map View
    m = folium.Map(location=d['coords'], zoom_start=12)
    folium.Marker(d['coords'], tooltip="CLIENT", icon=folium.Icon(color='red', icon='briefcase', prefix='fa')).add_to(m)
    
    for s in d['stations']:
        folium.Marker([s['lat'], s['lng']], tooltip=s['name'], icon=folium.Icon(color='blue', icon='gas-pump', prefix='fa')).add_to(m)
    
    st_folium(m, width="100%", height=500, key="main_map")

    # 2. Distance Matrix Table
    st.subheader("📊 Strategic Distance Matrix")
    matrix_df = pd.DataFrame([
        {
            "Station Name": s['name'],
            "Travel Distance": s['road_dist'],
            "Driving Time": s['duration'],
            "Direct Dist (km)": s['air_dist'],
            "Verified": "✅" if s['is_verified'] else "❓"
        } for s in d['stations']
    ])
    st.table(matrix_df)

    # 3. Location Cards
    st.subheader("🏁 Recommended Station Details")
    grid = st.columns(2)
    for i, s in enumerate(d['stations']):
        with grid[i % 2]:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 10px; background-color: #fcfcfc;">
                <h4 style="margin:0; color:#003399;">{s['name']}</h4>
                <p style="font-size:0.9em; color:#555;">{s['address']}</p>
                <b>Route:</b> {s['road_dist']} | <b>ETA:</b> {s['duration']}
            </div>
            """, unsafe_allow_html=True)
            st.image(f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={s['lat']},{s['lng']}&key={GOOGLE_API_KEY}")
