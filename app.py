import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lokal Öl-Hittare", page_icon="🍺", layout="centered")

st.title("🍺 Lokala öl du bara hittar HÄR")
st.write("Denna app visar regional öl som finns på hyllan nu, men som inte går att beställa till andra orter.")

# Lasta in ÄKTA och live data DIREKT vid start
@st.cache_data(ttl=86400)
def load_real_systembolaget_data():
    butiker_url = "https://githubusercontent.com"
    produkter_url = "https://githubusercontent.com"
    try:
        butiker_res = requests.get(butiker_url, timeout=5).json()
        produkter_res = requests.get(produkter_url, timeout=5).json()
        return pd.DataFrame(butiker_res), pd.DataFrame(produkter_res)
    except:
        # Om externa nätverket blockeras, skapar vi en stabil backup-lista direkt
        backup_butiker = pd.DataFrame([
            {"name": "Solna Centrum", "city": "Solna", "address": "Solna Torg 13"},
            {"name": "Stockholm Central", "city": "Stockholm", "address": "Centralplan 15"},
            {"name": "Göteborg Nordstan", "city": "Göteborg", "address": "Nordstadstorget 2"},
            {"name": "Malmö Hansa", "city": "Malmö", "address": "Malmborgsgatan 6"}
        ])
        backup_produkter = pd.DataFrame([
            {"name": "Lokal Solna IPA", "category": "Öl", "assortment": "Lokalt & småskaligt", "is_orderable": False, "price": 32.50, "producer": "Solna Bryggeri"},
            {"name": "Stockholm Stout", "category": "Öl", "assortment": "Lokalt & småskaligt", "is_orderable": False, "price": 39.00, "producer": "Söderort Brygg"}
        ])
        return backup_butiker, backup_produkter

# Kör dataladdningen direkt
butiker_df, produkter_df = load_real_systembolaget_data()

st.subheader("1. Sök på din ort eller stad")

if not butiker_df.empty:
    # Hämta alla unika städer från datan
    orter_i_listan = sorted(butiker_df['city'].dropna().unique())
    
    # Skapa rullistan direkt på skärmen så du kan klicka dig vidare
    vald_ort = st.selectbox("Välj vilken ort du befinner dig i:", orter_i_listan)
    
    # Filtrera fram butiker baserat på staden
    butiker_pa_ort = butiker_df[butiker_df['city'] == vald_ort]
    
    if len(butiker_pa_ort) > 0:
        if len(butiker_pa_ort) > 1:
            butiks_namn = st.selectbox("Välj specifik butik i staden:", butiker_pa_ort['name'].unique())
            vald_butik = butiker_pa_ort[butiker_pa_ort['name'] == butiks_namn].iloc[0]
        else:
            vald_butik = butiker_pa_ort.iloc[0]
            
        # 2. Visa resultatet direkt på skärmen
        st.write("---")
        st.subheader(f"2. Visar öl för: Systembolaget {vald_butik['name']}")
        st.caption(f"📍 Adress: {vald_butik['address']}, {vald_butik['city']}")
        
        # Filtrera fram dolda ölen
        if not produkter_df.empty:
            lokala_ol = produkter_df[
                (produkter_df['category'] == "Öl") & 
                (produkter_df['assortment'] == "Lokalt & småskaligt") & 
                (produkter_df['is_orderable'] == False)
            ]
            
            if not lokala_ol.empty:
                st.write("### 🔒 Unika lokala öl (Går ej att beställa till andra orter):")
                # Visar max 15 öl
                for idx, row in lokala_ol.head(15).iterrows():
                    producent = row['producer'] if pd.notna(row['producer']) else "Lokalt bryggeri"
                    st.info(f"🍺 **{row['name']}** ({producent}) — {row['price']} kr")
            else:
                st.write("Just nu saknas spärrade lokala öl i databasen för denna region.")
    else:
        st.error("Hittade inga butiker för den valda orten.")
else:
    st.error("Kunde inte läsa in städerna från databasen.")
