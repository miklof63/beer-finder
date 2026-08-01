
import streamlit as st
import pandas as pd
import requests
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Lokal Öl-Hittare", page_icon="🍺", layout="centered")

st.title("🍺 Lokala öl du bara hittar HÄR")
st.write("Denna app visar regional öl som finns på hyllan nu, men som inte går att beställa till andra orter.")

# 1. Hämta GPS-koordinater från iPhonens webbläsare
st.subheader("1. Hitta din position")
location = streamlit_js_eval(data_string="username", component_mode="get_geolocation", key="geo")

if location:
    lat = location['coords']['latitude']
    lon = location['coords']['longitude']
    st.success(def_msg := f"Position hittad! (Lat: {lat:.4f}, Lon: {lon:.4f})")
    
    # 2. Lasta in Systembolagets data (Simulerat flöde från JSON-dump)
    # I en skarp app ersätter vi detta med öppna JSON-länkar från t.ex. GitHub
    @st.cache_data(ttl=86400) # Sparar datan i 24 timmar så det går blixtsnabbt
    def load_systembolaget_data():
        # Här laddas produkt- och butiksdata in
        # För demonstration skapar vi ett litet exempel:
        butiker = pd.DataFrame([
            {"butik_id": "0102", "namn": "Hagalund, Solna", "lat": 59.3642, "lon": 18.0125},
            {"butik_id": "0205", "namn": "Stockholm City", "lat": 59.3326, "lon": 18.0649}
        ])
        
        produkter = pd.DataFrame([
            {"namn": "Hagalunds Lokala IPA", "butik_id": "0102", "typ": "Lokalt & småskaligt", "orderbar": False},
            {"namn": "Solna Lager", "butik_id": "0102", "typ": "Lokalt & småskaligt", "orderbar": True},
            {"namn": "City Brygg", "butik_id": "0205", "typ": "Lokalt & småskaligt", "orderbar": False}
        ])
        return butiker, produkter

    butiker_df, produkter_df = load_systembolaget_data()

    # 3. Matte för att hitta närmaste butik utifrån GPS
    butiker_df['distans'] = ((butiker_df['lat'] - lat)**2 + (butiker_df['lon'] - lon)**2)**0.5
    narmaste_butik = butiker_df.sort_values(by='distans').iloc[0]
    
    st.subheader(f"2. Din närmaste butik: {narmaste_butik['namn']}")
    
    # 4. Filtrera fram öl: Måste matcha butiken, vara "Lokalt & småskaligt" och INTE vara orderbar
    lokal_ol = produkter_df[
        (produkter_df['butik_id'] == narmaste_butik['butik_id']) & 
        (produkter_df['typ'] == "Lokalt & småskaligt") & 
        (produkter_df['orderbar'] == False)
    ]

    # 5. Visa resultatet
    st.subheader("3. Unika lokala öl i denna butik:")
    if not lokal_ol.empty:
        for idx, row in lokal_ol.iterrows():
            st.info(f"🔒 **{row['namn']}** – Säljs endast i denna butik!")
    else:
        st.write("Just nu hittades inga unika lokala öl som är spärrade för beställning i denna butik.")

else:
    st.info("Klicka på tillåt i rutan som dyker upp för att dela din GPS-position, eller vänta på att mobilen hittar din plats.")
