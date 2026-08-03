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
        # 3. LÄS IN SPARADE INSTÄLLNINGAR FRÅN URL:EN (BFF-FRONTEND LOGIK)
        params = st.query_params
        
        # Hämta sparade stilar
        sparade_stilar_raw = params.get("stil", "")
        sparade_stilar = [s.strip() for s in sparade_stilar_raw.split(",") if s.strip()] if sparade_stilar_raw else None

        # Hämta sparade smakklockor (omvandla till heltal, sök efter defaults om de saknas)
        def_beska = int(params.get("beska", 0))
        def_fyllighet = int(params.get("fyll", 0))
        def_sotma = int(params.get("sotma", 12))

        # 4. SÖKFÄLT FÖR ANVÄNDAREN
        st.subheader("Filtrera och sök")
        
        # Dynamiskt hämta de ölstilar som faktiskt finns i vårt matchade resultat
        tillgangliga_stilar = sorted(unika_ol['categoryLevel2'].unique())

        default_val = [s for s in sparade_stilar if s in tillgangliga_stilar] if sparade_stilar else None

        # Skapa en flervalsmeny (multiselect) – förvald med alla stilar
        valda_stilar = st.multiselect(
            "Filtrera på specifika ölstilar (lämna tom för att visa alla):",
            options=tillgangliga_stilar,
            default=default_val
        )
        # Skjutreglage för smakklockor (0-12, där 0 betyder "Filtrera inte")
        st.write("**Justera smakprofil (0-12):**")
        min_beska = st.slider("Minsta beska (bitterness:)", 0, 12, def_beska)
        min_fyllighet = st.slider("Minsta fyllighet (body):", 0, 12, def_fyllighet)
        max_sotma = st.slider("Maximal sötma (sweetness):", 0, 12, def_sotma)
        
        # Sökfält för fritext (bryggeri eller stad)
        sokning = st.text_input("Skriv t.ex. namnet på ett bryggeri eller en ort (t.ex. Solna, Uppsala, Poppels):", "")

        # 5. KNAPP FÖR ATT SPARA INSTÄLLNINGARNA TILL ADRESSFÄLTET
        if st.button("💾 Spara mina inställningar som förval"):
            # Spara den första valda stilen om det finns någon, annars tomt
            aktuell_stil = ",".join(valda_stilar) if valda_stilar else ""
            
            # Skriv värdena direkt till URL-fältet i webbläsaren
            st.query_params.update({
                "stil": aktuell_stil,
                "beska": min_beska,
                "fyll": min_fyllighet,
                "sotma": max_sotma
            })
            st.success("Inställningarna sparade i adressfältet! Spara sidan som bokmärke på hemskärmen i din iPhone för att alltid starta så här. 🚀")

        # Applicera användarens valda filter
        if valda_stilar:
            unika_ol = unika_ol[unika_ol['categoryLevel2'].isin(valda_stilar)]
            
        # Applicera smakklockornas filter på datan (omvandla till siffror först)
        unika_ol['tasteClockBitter'] = pd.to_numeric(unika_ol['tasteClockBitter'], errors='coerce').fillna(0)
        unika_ol['tasteClockBody'] = pd.to_numeric(unika_ol['tasteClockBody'], errors='coerce').fillna(0)
        unika_ol['tasteClockSweetness'] = pd.to_numeric(unika_ol['tasteClockSweetness'], errors='coerce').fillna(0)

        unika_ol = unika_ol[
            (unika_ol['tasteClockBitter'] >= min_beska) &
            (unika_ol['tasteClockBody'] >= min_fyllighet) &
            (unika_ol['tasteClockSweetness'] <= max_sotma)
        ]

        if sokning:
            unika_ol = unika_ol[
                (unika_ol['productNameBold'].astype(str).str.contains(sokning, na=False, case=False)) |
                (unika_ol['producerName'].astype(str).str.contains(sokning, na=False, case=False)) |
                (unika_ol['productNameThin'].astype(str).str.contains(sokning, na=False, case=False)) |
                (unika_ol['country'].astype(str).str.contains(sokning, na=False, case=False)) |
                (unika_ol['originLevel1'].astype(str).str.contains(sokning, na=False, case=False)) |
                (unika_ol['originLevel2'].astype(str).str.contains(sokning, na=False, case=False))
            ]
            
        # Sortera i bokstavsordning på ölets namn
        if not unika_ol.empty:
            unika_ol = unika_ol.sort_values(by="productNameBold")

        # 6. VISA RESULTATET
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
                
                # Hämta ursprung (län och kommun)
                lan = row.get('originLevel1', '')
                kommun = row.get('originLevel2', '')
                ursprung_delar = []
                if pd.notna(lan) and lan != "" and lan != "None":
                    ursprung_delar.append(str(lan))
                if pd.notna(kommun) and kommun != "" and kommun != "None":
                    ursprung_delar.append(str(kommun))
                ursprung_text = f" | 📍 **Ursprung:** {', '.join(ursprung_delar)}" if ursprung_delar else ""
                
                st.info(
                    f"🍺 **{namn}** *{tillägg_text}*\n\n"
                    f"**Stil:** {stil} | **Bryggeri:** {bryggeri_text}{ursprung_text}  \n"
                    f"**Pris:** {pris} kr | **Styrka:** {alkohol}% | **Storlek:** {volym}\n\n"
                    f"🔗 [Visa på Systembolaget.se]({direct_url})"
                )
        else:
            st.write("Inga unika, spärrade öl matchade din sökning just nu.")

    except Exception as err:
        st.error(f"Ett fel uppstod vid filtreringen: {err}")
else:
    st.info("Kunde inte ladda in produkter. Testa att uppdatera sidan.")
