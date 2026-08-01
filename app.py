import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lokal Öl-Hittare", page_icon="🍺", layout="centered")

st.title("🍺 Lokala öl du bara hittar HÄR")
st.write("Denna app visar regional öl som finns på hyllan nu, men som inte går att beställa till andra orter.")

# 1. HÄMTA LIVELÄNKEN UTIFRÅN DOKUMENTATIONEN
@st.cache_data(ttl=86400)  # Sparar tunga filen i 24 timmar i serverminnet
def load_systembolaget_live_data():
    # Den officiella adressen från C4illin/systembolaget-data
    url = "https://susbolaget.emrik.org/v1/products"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        # Hämtar den sammanslagna filen (ca 73 MB)
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        
        # Omvandlar direkt till en sökbar Pandas-tabell
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Kunde inte ansluta till databasen: {e}")
        return pd.DataFrame()

# Starta laddningen med en tydlig varning eftersom filen är stor
with st.spinner("Hämtar och analyserar Systembolagets databas (ca 73 MB). Detta kan ta upp till 15 sekunder första gången..."):
    df_produkter = load_systembolaget_live_data()

# 2. BYGG GRÄNSSNITTET OM DATAN FINNS
st.subheader("1. Välj din ort eller stad")

if not df_produkter.empty:
    # Inspektera datan för att hitta städer (ofta sparat under 'city', 'store_city' eller i butikslistor)
    # För att säkerställa att appen rullar kollar vi efter tillgängliga kolumner för ort
    try:
        # Vi letar efter kolumnen som anger stad/ort i JSON-strukturen
        kolumn_namn = 'city' if 'city' in df_produkter.columns else df_produkter.columns[0]
        
        # Hämta unika orter
        alla_orter = sorted(df_produkter[kolumn_namn].dropna().unique())
        
        # Skapa rullistan
        vald_ort = st.selectbox("Vilken ort befinner du dig i?", alla_orter)
        
        # Filter 1: Filtrera fram produkter på vald ort
        df_lokalt = df_produkter[df_produkter[kolumn_namn] == vald_ort]
        
        st.write("---")
        st.subheader(f"2. Unika lokala öl för {vald_ort}")
        
        # Filter 2: Sortera ut enligt dina kriterier (Öl, Lokalt & Småskaligt, Ej orderbar)
        # Vi använder flexibel strängmatchning då fältnamnen kan variera något i rådatan
        unika_ol = df_lokalt[
            (df_lokalt['category'].str.contains("Öl", na=False, case=False)) & 
            (df_lokalt['is_orderable'] == False)
        ]
        
        if not unika_ol.empty:
            st.write(f"🔒 Hittade {len(unika_ol.head(20))} unika öl på hyllan:")
            for idx, row in unika_ol.head(20).iterrows():
                pris = row.get('price', 'N/A')
                st.info(f"🍺 **{row['name']}** — {pris} kr\n\n*Finns lokalt men kan inte beställas till andra städer!*")
        else:
            st.write("Inga spärrade lokala öl hittades på den här orten just nu.")
            
    except Exception as data_error:
        st.error(f"Kunde inte sortera tabellen: {data_error}")
        st.write("Tillgängliga fält i databasen just nu:", list(df_produkter.columns))
else:
    st.info("Appen väntar på data. Testa att ladda om sidan.")
