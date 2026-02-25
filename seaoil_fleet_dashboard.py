import streamlit as st
import requests
import re
import pandas as pd
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium

GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]

# Your verified list
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

st.set_page_config(page_title="Seaoil Fleet Intelligence", layout="wide")

# Initialize session state so results persist
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# --- Logic Functions ---

def parse_coords(url):
    regex = r"@(-?\d+\.\d+),(-?\d+\.\d+)"
    match = re.search(regex, url)
    return (float(match.group(1)), float(match.group(2))) if match else None

def get_distance_data(origin_coords, destinations):
    """Calls Google Distance Matrix API for real-world travel times."""
    dest_strings = [f"{d['coords'][0]},{d['coords'][1]}" for d in destinations]
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{origin_coords[0]},{origin_coords[1]}",
        "destinations": "|".join(dest_strings),
        "key": GOOGLE_API_KEY
    }
    data = requests.get(url, params=params).json()
    
    results = []
    if data['status'] == 'OK':
        elements = data['rows'][0]['elements']
        for i, element in enumerate(elements):
            if element['status'] == 'OK':
                results.append({
                    "distance_text": element['distance']['text'],
                    "duration_text": element['duration']['text']
                })
            else:
                results.append({"distance_text": "N/A", "duration_text": "N/A"})
    return results

def get_top_seaoil(coords):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": "SEAOIL", "location": f"{coords[0]},{coords[1]}", "radius": 15000, "key": GOOGLE_API_KEY}
    raw_results = requests.get(url, params=params).json().get("results", [])
    
    scored = []
    for s in raw_results:
        s_name = s['name'].upper()
        s_coords = (s['geometry']['location']['lat'], s['geometry']['location']['lng'])
        dist_air = geodesic(coords, s_coords).km
        
        # Verify if it's in your provided branch list
        is_verified = any(branch.split(" - ")[0] in s_name for branch in RAW_BRANCHES)
        
        score = 0
        if is_verified: score += 70
        if dist_air <= 5: score += 20
        
        scored.append({
            "name": f"SEAOIL - {s['name'].replace('Seaoil', '').replace('-', '').strip()}",
            "addr": s.get('formatted_address', ''),
            "dist_air": round(dist_air, 2),
            "score": score,
            "coords": s_coords
        })
    
    top_6 = sorted(scored, key=lambda x: (-x['score'], x['dist_air']))[:6]
    
    # Enrich with Distance Matrix
    dist_matrix = get_distance_data(coords, top_6)
    for i, item in enumerate(dist_matrix):
        top_6[i]['real_dist'] = item['distance_text']
        top_6[i]['duration'] = item['duration_text']
        
    return top_6

# --- UI ---

st.title("Seaoil Strategic Mapping Tool")
url_input = st.text_input("Paste Google Maps URL (@lat,long)")

if st.button("Analyze Fleet Proximity"):
    coords = parse_coords(url_input)
    if coords:
        with st.spinner("Calculating Distance Matrix & Fetching Stations..."):
            st.session_state.analysis_results = {
                "client_coords": coords,
                "stations": get_top_seaoil(coords)
            }
    else:
        st.error("Invalid URL. Ensure it contains the @lat,long coordinates.")

# Display results if they exist in state
if st.session_state.analysis_results:
    res = st.session_state.analysis_results
    client_coords = res["client_coords"]
    stations = res["stations"]

    # 1. THE MAP (Fixed with unique key to prevent flashing)
    m = folium.Map(location=client_coords, zoom_start=12)
    folium.Marker(client_coords, icon=folium.Icon(color='red', icon='briefcase', prefix='fa'), tooltip="CLIENT").add_to(m)
    for s in stations:
        folium.Marker(s['coords'], tooltip=s['name'], icon=folium.Icon(color='blue', icon='gas-pump', prefix='fa')).add_to(m)
    
    st_folium(m, width="100%", height=500, key="stable_map")

    # 2. DISTANCE MATRIX TABLE
    st.subheader("📊 Strategic Distance Matrix")
    matrix_data = []
    for s in stations:
        matrix_data.append({
            "Station Name": s['name'],
            "Travel Distance": s['real_dist'],
            "Estimated Time": s['duration'],
            "Straight-Line (km)": s['dist_air'],
            "Strategic Score": f"{s['score']}/100"
        })
    st.table(pd.DataFrame(matrix_data))

    # 3. LOCATION CARDS & STREET VIEW
    st.subheader("📍 Detailed Station Profiles")
    cols = st.columns(2)
    for idx, s in enumerate(stations):
        with cols[idx % 2]:
            st.markdown(f"""
            <div style="border:1px solid #ddd; padding:15px; border-radius:10px; margin-bottom:10px; background-color: #f9f9f9;">
                <h4 style="color:#003399; margin-bottom:2px;">{s['name']}</h4>
                <p style="font-size:0.85em; color:gray;">{s['addr']}</p>
                <b>Real Distance:</b> {s['real_dist']} | <b>Travel Time:</b> {s['duration']}
            </div>
            """, unsafe_allow_html=True)
            st.image(f"https://maps.googleapis.com/maps/api/streetview?size=600x300&location={s['coords'][0]},{s['coords'][1]}&key={GOOGLE_API_KEY}")
