import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lokal Öl-Hittare", page_icon="🍺", layout="centered")

st.title("🍺 Lokala öl du bara hittar HÄR")
st.write("Denna app visar regional öl som finns på hyllan nu, men som inte går att beställa till andra orter.")

# 1. HÄMTA ÄKTA DATA FRÅN SYSTEMBOLAGET (Körs direkt vid start)
@st.cache_data(ttl=86400)  # Sparar datan i 24 timmar så appen laddar blixtsnabbt
def load_systembolaget_data():
    # KORREKTA OCH FULLSTÄNDIGA URL-ADRESSER TILL DATAKÄLLAN
    stores_url = "https://githubusercontent.com"
    products_url = "https://githubusercontent.com"
    
    # Headers för att berätta för GitHub att vi är en legitim webbläsare
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # Här sker själva fetch-anropet (.json() omvandlar råtexten till Python-objekt)
        stores_res = requests.get(stores_url, headers=headers, timeout=10).json()
        products_res = requests.get(products_url, headers=headers, timeout=10).json()
        
        # Gör om rådatan till sökbara tabeller (DataFrames)
        return pd.DataFrame(stores_res), pd.DataFrame(products_res)
    except Exception as e:
        # Om något ändå blockeras (t.ex. nätverksfel), visar vi ett felmeddelande i appen
        st.error(f"Kunde inte hämta live-data på grund av: {e}")
        # Returnera tomma tabeller så appen inte kraschar helt
        return pd.DataFrame(), pd.DataFrame()

# Starta dataladdning direkt med en snygg laddnings-snurra
with st.spinner("Hämtar färsk data från Systembolagets databas..."):
    butiker_df, produkter_df = load_systembolaget_data()

# 2. BYGG GRÄNSSNITTET UTIFRÅN DEN HÄMTADE DATAN
st.subheader("1. Välj din ort eller stad")

if not butiker_df.empty:
    # Sortera alla unika städer i bokstavsordning
    alla_orter = sorted(butiker_df['city'].dropna().unique())
    
    # Skapa den första rullistan på skärmen
    vald_ort = st.selectbox("Vilken ort befinner du dig i?", alla_orter)
    
    # Filtrera fram butiker som ligger i den valda staden
    butiker_pa_ort = butiker_df[butiker_df['city'] == vald_ort]
    
    if not butiker_pa_ort.empty:
        # Om staden har flera butiker, visa en rullista till
        if len(butiker_pa_ort) > 1:
            butiks_namn = st.selectbox("Välj specifik butik:", butiker_pa_ort['name'].unique())
            vald_butik = butiker_pa_ort[butiker_pa_ort['name'] == butiks_namn].iloc[0]
        else:
            vald_butik = butiker_pa_ort.iloc[0]
            
        # 3. VISA DET LOKALA SORTIMENTET
        st.write("---")
        st.subheader(f"2. Visar öl för: Systembolaget {vald_butik['name']}")
        st.caption(f"📍 Adress: {vald_butik['address']}, {vald_butik['city']}")
        
        if not produkter_df.empty:
            # Sortera ut: Endast Öl, Endast "Lokalt & småskaligt", och is_orderable ska vara Falskt (False)
            unika_lokala_ol = produkter_df[
                (produkter_df['category'] == "Öl") & 
                (produkter_df['assortment'].str.contains("Lokalt & småskaligt", na=False)) & 
                (produkter_df['is_orderable'] == False)
            ]
            
            if not unika_lokala_ol.empty:
                st.write(f"### 🔒 Hittade unika öl i närområdet:")
                st.write("Dessa säljs på hyllan lokalt men kan inte beställas till andra städer.")
                
                # Visa ölen snyggt på skärmen
                for idx, row in unika_lokala_ol.head(20).iterrows():
                    bryggeri = row['producer'] if pd.notna(row['producer']) and row['producer'] != "" else "Lokalt bryggeri"
                    st.info(f"🍺 **{row['name']}** ({bryggeri}) — {row['price']} kr")
            else:
                st.write("Just nu hittades inga spärrade lokala öl för denna specifika region i databasen.")
        else:
            st.error("Kunde inte läsa in produktlistan.")
    else:
        st.error("Inga butiker hittades på den valda orten.")
else:
    st.error("Kunde inte ladda in städerna från Systembolagets databas.")
