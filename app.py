import streamlit as st
import pandas as pd
import requests
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Lokal Öl-Hittare", page_icon="🍺", layout="centered")

st.title("🍺 Lokala öl du bara hittar HÄR")
st.write("Denna app visar regional öl som finns på hyllan nu, men som inte går att beställa till andra orter.")

# Lasta in ÄKTA och live data från öppna databaser (Hämtas en gång om dygnet)
@st.cache_data(ttl=86400)
def load_real_systembolaget_data():
    butiker_url = "https://githubusercontent.com"
    produkter_url = "https://githubusercontent.com"
    try:
        butiker_res = requests.get(butiker_url).json()
        produkter_res = requests.get(produkter_url).json()
        return pd.DataFrame(butiker_res), pd.DataFrame(produkter_res)
    except:
        return pd.DataFrame(), pd.DataFrame()

with st.spinner("Laddar Systembolagets databas..."):
    butiker_df, produkter_df = load_real_systembolaget_data()

# Hantering av sökmetod
st.subheader("1. Välj hur appen ska hitta din butik")
metod = st.radio("Metod:", ["Sök på ort/stad", "Använd min GPS (Mobil/Dator)"], horizontal=True)

vald_butik = None

if metod == "Sök på ort/stad":
    if not butiker_df.empty:
        # Skapa en lista med alla städer/orter för rullistan
        orter = sorted(butiker_df['city'].dropna().unique())
        vald_ort = st.selectbox("Vilken ort befinner du dig i?", orter)
        
        # Filtrera fram butiker på den orten
        butiker_pa_ort = butiker_df[butiker_df['city'] == vald_ort]
        
        if len(butiker_pa_ort) > 1:
            butiks_val = st.selectbox("Välj specifik butik:", butiker_pa_ort['name'].unique())
            vald_butik = butiker_pa_ort[butiker_pa_ort['name'] == butiks_val].iloc[0]
        else:
            vald_butik = butiker_pa_ort.iloc[0]
            
else:
    # GPS-spåret
    hitta_gps = st.button("📍 Starta GPS-sökning")
    if hitta_gps or st.session_state.get('geo_retrieved', False):
        location = streamlit_js_eval(data_string="username", component_mode="get_geolocation", key="geo")
        if location:
            st.session_state['geo_retrieved'] = True
            lat = location['coords']['latitude']
            lon = location['coords']['longitude']
            st.success(f"GPS hittad! (Lat: {lat:.2f}, Lon: {lon:.2f})")
            
            # Räkna ut närmaste butik
            butiker_df['distans'] = ((butiker_df['latitude'].astype(float) - lat)**2 + (butiker_df['longitude'].astype(float) - lon)**2)**0.5
            vald_butik = butiker_df.sort_values(by='distans').iloc[0]
        else:
            st.info("Väntar på att webbläsaren ska svara med din GPS-position...")

# 2. Visa resultatet om en butik har identifierats
if vald_butik is not None:
    st.subheader(f"2. Butik vald: Systembolaget {vald_butik['name']}")
    st.write(f"📍 {vald_butik['address']}, {vald_butik['city']}")
    
    # FILTRERING: Hitta öl som är Lokalt & Småskaligt och INTE orderbar
    if not produkter_df.empty:
        lokala_ol = produkter_df[
            (produkter_df['category'] == "Öl") & 
            (produkter_df['assortment'] == "Lokalt & småskaligt") & 
            (produkter_df['is_orderable'] == False)
        ]
        
        st.subheader("3. Unika lokala öl (Går ej att beställa till andra orter):")
        
        if not lokala_ol.empty:
            # Visar de 15 första unika lokala ölen i sortimentet
            for idx, row in lokala_ol.head(15).iterrows():
                producer_info = row['producer'] if pd.notna(row['producer']) else "Lokalt bryggeri"
                st.info(f"🔒 **{row['name']}** ({producer_info}) — {row['price']} kr")
        else:
            st.write("Inga spärrade lokala öl hittades i databasen just nu.")
    else:
        st.error("Kunde inte läsa in produktdatan.")
