import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Lokal Öl-Hittare", page_icon="🍺", layout="centered")

st.title("🍺 Unika lokala öl i Sverige")
st.write("Denna app visar hantverksöl som är regionalt begränsade på hyllorna och som INTE går att beställa till andra delar av landet.")

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
with st.spinner("Hämtar och sorterar Systembolagets databas (ca 73 MB)..."):
    df = load_systembolaget_products()

# 2. FILTRERA FRAM DE UNIKE ÖLEN UTIFRÅN SYSTEMBOLAGETS FÄLT
if not df.empty:
    try:
        # Sortera ut enligt dina exakta fältnamn: 
        # Endast Öl, Regionalt spärrade (isRegionalRestricted), Ej orderbara till hela landet (is_orderable == False)
        unika_ol = df[
            (df['category'].str.contains("Öl", na=False, case=False)) & 
            (df['isRegionalRestricted'] == True) & 
            (df['is_orderable'] == False)
        ]
        
        # Sortera så nyaste eller dyraste/billigaste ligger logiskt, eller bara i bokstavsordning
        unika_ol = unika_ol.sort_values(by="productNameBold")

        # 3. SÖKFÄLT FÖR ANVÄNDAREN
        st.subheader("Filtrera på bryggeri, stad eller namn")
        sokning = st.text_input("Skriv t.ex. namnet på ett bryggeri eller en ort (t.ex. Solna, Göteborg, Poppels):", "")

        if sokning:
            # Sök i både produktnamn och producentens namn
            unika_ol = unika_ol[
                (unika_ol['productNameBold'].str.contains(sokning, na=False, case=False)) |
                (unika_ol['producerName'].str.contains(sokning, na=False, case=False))
            ]

        # 4. VISA RESULTATET
        st.write("---")
        st.subheader(f"Hittade {len(unika_ol)} unika öl")
        
        if not unika_ol.empty:
            # Visa de första 30 träffarna snyggt
            for idx, row in unika_ol.head(30).iterrows():
                namn = row['productNameBold']
                tillägg = row['productNameThin'] if pd.notna(row['productNameThin']) else ""
                bryggeri = row['producerName'] if pd.notna(row['producerName']) else "Lokalt bryggeri"
                pris = row['price']
                alkohol = row['alcoholPercentage']
                volym = row['volumeText']
                
                # Visa snygga informationsboxar
                st.info(
                    f"🍺 **{namn}** *{tillägg}*\n\n"
                    f"**Bryggeri:** {bryggeri}  \n"
                    f"**Pris:** {pris} kr | **Styrka:** {alkohol}% | **Storlek:** {volym}\n\n"
                    f"*🔒 Säljs endast lokalt på hyllan vid sitt bryggeri!*"
                )
        else:
            st.write("Inga unika, spärrade öl matchade din sökning just nu.")

    except Exception as err:
        st.error(f"Ett fel uppstod vid filtreringen: {err}")
else:
    st.info("Kunde inte ladda in produkter. Testa att uppdatera sidan.")
