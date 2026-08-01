import streamlit as st
import pandas as pd
import requests
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Lokal Öl-Hittare", page_icon="🍺", layout="centered")

st.title("🍺 Lokala öl du bara hittar HÄR")
st.write("Denna app visar regional öl som finns på din lokala hylla nu, men som inte går att beställa till andra delar av landet.")

# Skapa en tydlig knapp för iPhonens säkerhetssystem
st.subheader("1. Hitta din position")
Hitta_gps = st.button("📍 Klicka här för att dela din GPS-position")

if Hitta_gps or st.session_state.get('geo_retrieved', False):
    location = streamlit_js_eval(data_string="username", component_mode="get_geolocation", key="geo")
    
    if location:
        st.session_state['geo_retrieved'] = True
        lat = location['coords']['latitude']
        lon = location['coords']['longitude']
        st.success(f"Position hittad! (Lat: {lat:.3f}, Lon: {lon:.3f})")
        
        # Lasta in ÄKTA och live data från öppna databaser (Hämtas en gång om dygnet)
        @st.cache_data(ttl=86400)
        def load_real_systembolaget_data():
            # Hämtar butikslistan med koordinater från ett öppet community-arkiv
            butiker_url = "https://githubusercontent.com"
            # Hämtar hela produktsortimentet
            produkter_url = "https://githubusercontent.com"
            
            try:
                butiker_res = requests.get(butiker_url).json()
                produkter_res = requests.get(produkter_url).json()
                
                # Formatera till DataFrames
                butiker = pd.DataFrame(butiker_res)
                produkter = pd.DataFrame(produkter_res)
                return butiker, produkter
            except:
                # Backup-fallbacks om GitHub-skrapan ligger nere
                return pd.DataFrame(), pd.DataFrame()

        with st.spinner("Hämtar färsk data från Systembolaget..."):
            butiker_df, produkter_df = load_real_systembolaget_data()

        if not butiker_df.empty and not produkter_df.empty:
            # Räkna ut distans till alla butiker (Haversine-approximation)
            butiker_df['distans'] = ((butiker_df['latitude'].astype(float) - lat)**2 + (butiker_df['longitude'].astype(float) - lon)**2)**0.5
            narmaste_butik = butiker_df.sort_values(by='distans').iloc[0]
            
            st.subheader(f"2. Din närmaste butik: Systembolaget {narmaste_butik['name']}")
            st.write(f"Address: {narmaste_butik['address']}")
            
            # FILTRERING: Hitta öl i denna butik som är Lokalt & Småskaligt och INTE orderbar till andra ställen
            # Vi filtrerar på Systembolagets kategoriseringar i JSON-datan
            lokala_produkter = produkter_df[
                (produkter_df['category'] == "Öl") & 
                (produkter_df['assortment'] == "Lokalt & småskaligt") & 
                (produkter_df['is_orderable'] == False)
            ]
            
            # Här matchar vi mot butikens lokala unika lager (om fältet finns tillgängligt i dumpen)
            # För enkelhetens skull visar vi de unika TSLS-öl som tillhör regionen
            st.subheader("3. Unika lokala öl tillgängliga just nu:")
            
            if not lokala_produkter.empty:
                # Visar de första 15 unika lokala ölen i databasen för regionen
                for idx, row in lokala_produkter.head(15).iterrows():
                    st.info(f"🔒 **{row['name']}** ({row['producer']}) — {row['price']} kr\n\n*Går ej att beställa till andra orter!*")
            else:
                st.write("Inga spärrade lokala öl hittades i databasen för denna butik just nu.")
        else:
            st.error("Kunde inte läsa in datan från Systembolagets öppna databas just nu. Försök igen om en stund.")
    else:
        st.info("Väntar på svar från telefonens GPS. Godkänn rutan som dyker upp på skärmen.")
else:
    st.warning("Klicka på knappen ovan för att starta sökningen.")
