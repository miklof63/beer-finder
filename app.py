import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Lokal Öl-Hittare", page_icon="🍺", layout="centered")

st.title("🍺 Unika lokala öl i Sverige")
st.write("Denna app visar hantverksöl som är regionalt begränsade på hyllorna.")

# 1. HÄMTA SYSTEMBOLAGETS PRODUKTER
@st.cache_data(ttl=86400)  # Sparar datan i 24 timmar i serverminnet
def load_systembolaget_products():
    url = "https://susbolaget.emrik.org/v1/products"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        df = pd.DataFrame(response.json())
        return df
    except Exception as e:
        st.error(f"Kunde inte ansluta till databasen: {e}")
        return pd.DataFrame()

# Laddningssnurra
with st.spinner("Hämtar och analyserar Systembolagets databas (ca 73 MB)..."):
    df = load_systembolaget_products()

# 2. FILTRERA FRAM DE UNIKA ÖLEN
if not df.empty:
    try:
        # Omvandla de fält som faktiskt finns till textsträngar
        df['productNameBold'] = df['productNameBold'].astype(str)
        df['isRegionalRestricted'] = df['isRegionalRestricted'].astype(str)
        df['assortmentText'] = df['assortmentText'].astype(str)
        df['isCompletelyOutOfStock'] = df['isCompletelyOutOfStock'].astype(str)
        
        # Datumfiltrering: Omvandla lanseringsdatum till datumobjekt
        df['productLaunchDate'] = pd.to_datetime(df['productLaunchDate'], errors='coerce')
        idag = pd.Timestamp(datetime.now().date())  
        
        # Eftersom 'category' är None, använder vi 'categoryLevel1' som innehåller ordet "Öl"
        if 'categoryLevel1' in df.columns:
            df['categoryLevel1'] = df['categoryLevel1'].astype(str)
            cat_filter = df['categoryLevel1'].str.contains("Öl", na=False, case=False)
        else:
            cat_filter = True  # Fallback om kolumnen saknas
        
        # Filtrera: Måste vara Öl (via categoryLevel1) och ha isRegionalRestricted='true'
        unika_ol = df[
            (cat_filter) & 
            (df['isRegionalRestricted'].str.lower() == 'true') &
            (df['assortmentText'].str.contains("Lokalt & småskaligt", na=False, case=False)) &
            (~df['isCompletelyOutOfStock'].str.lower().str.contains('true', na=False)) &
            (df['productLaunchDate'] <= idag)
        ]        
        
        # Sortera i bokstavsordning på ölets namn
        if not unika_ol.empty:
            unika_ol = unika_ol.sort_values(by="productNameBold")

        # 3. SÖKFÄLT FÖR ANVÄNDAREN
        st.subheader("Filtrera och sök")
        
        # Dynamiskt hämta de ölstilar som faktiskt finns i vårt matchade resultat
        tillgangliga_stilar = sorted(unika_ol['categoryLevel2'].unique())

        default_val = ["Ale"] if "Ale" in tillgangliga_stilar else None
        
        # Skapa en flervalsmeny (multiselect) – förvald med alla stilar
        valda_stilar = st.multiselect(
            "Filtrera på specifika ölstilar (lämna tom för att visa alla):",
            options=tillgangliga_stilar,
            default=default_val
        )
        
        sokning = st.text_input("Skriv t.ex. namnet på ett bryggeri eller en ort (t.ex. Solna, Uppsala, Poppels):", "")

        # Applicera användarens valda filter
        if valda_stilar:
            unika_ol = unika_ol[unika_ol['categoryLevel2'].isin(valda_stilar)]
            
        if sokning:
            unika_ol = unika_ol[
                (unika_ol['productNameBold'].astype(str).str.contains(sokning, na=False, case=False)) |
                (unika_ol['producerName'].astype(str).str.contains(sokning, na=False, case=False)) |
                (unika_ol['productNameThin'].astype(str).str.contains(sokning, na=False, case=False))
            ]

        # 4. VISA RESULTATET
        st.write("---")
        st.subheader(f"Hittade {len(unika_ol)} unika öl")
        
        if not unika_ol.empty:
            # Visa de första 30 träffarna snyggt på skärmen
            for idx, row in unika_ol.head(30).iterrows():
                namn = row.get('productNameBold', 'Okänt namn')
                tillägg = row.get('productNameThin', '')
                tillägg_text = tillägg if pd.notna(tillägg) else ""
                bryggeri = row.get('producerName', 'Lokalt bryggeri')
                bryggeri_text = bryggeri if pd.notna(bryggeri) else "Lokalt bryggeri"
                pris = row.get('price', 'N/A')
                alkohol = row.get('alcoholPercentage', 'N/A')
                volym = row.get('volumeText', '')
                stil = row.get('categoryLevel2', 'Öl')
                # Hämta artikelnumret från din JSON (t.ex. '3416414')
                artikel_nummer = row.get('productNumber', '')
                direct_url = f"https://www.systembolaget.se/produkt/ol/{artikel_nummer}/"
                
                st.info(
                    f"🍺 **{namn}** *{tillägg_text}*\n\n"
                    f"**Stil:** {stil} | **Bryggeri:** {bryggeri_text}  \n"
                    f"**Pris:** {pris} kr | **Styrka:** {alkohol}% | **Storlek:** {volym}\n\n"
                    f"🔗 [Visa på Systembolaget.se]({direct_url})"
                )
        else:
            st.write("Inga unika, spärrade öl matchade din sökning just nu.")

    except Exception as err:
        st.error(f"Ett fel uppstod vid filtreringen: {err}")
else:
    st.info("Kunde inte ladda in produkter. Testa att uppdatera sidan.")
