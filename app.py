import streamlit as st
import pandas as pd
import requests

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
        # Säkerställ att fälten tolkas korrekt som sanna/falska booleska värden
        df['isRegionalRestricted'] = df['isRegionalRestricted'].fillna(False).astype(bool)
        df['isTsLsAssortment'] = df['isTsLsAssortment'].fillna(False).astype(bool)
        df['category'] = df['category'].astype(str)
        
        # Superren och exakt filtrering: Måste vara Öl, och antingen regionalt låst ELLER tillhöra TSLS
        unika_ol = df[
            (df['category'].str.contains("Öl", na=False, case=False))
        ]
        
        # Sortera i bokstavsordning på ölets namn
        if not unika_ol.empty:
            unika_ol = unika_ol.sort_values(by="productNameBold")

        # 3. SÖKFÄLT FÖR ANVÄNDAREN
        st.subheader("Filtrera på bryggeri, stad eller namn")
        sokning = st.text_input("Skriv t.ex. namnet på ett bryggeri eller en ort (t.ex. Solna, Uppsala, Poppels):", "")

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
                
                st.info(
                    f"🍺 **{namn}** *{tillägg_text}*\n\n"
                    f"**Bryggeri:** {bryggeri_text}  \n"
                    f"**Pris:** {pris} kr | **Styrka:** {alkohol}% | **Storlek:** {volym}\n\n"
                    f"*🔒 Säljs lokalt på hyllan!*"
                )
        else:
            st.write("Inga unika, spärrade öl matchade din sökning just nu.")

    except Exception as err:
        st.error(f"Ett fel uppstod vid filtreringen: {err}")
else:
    st.info("Kunde inte ladda in produkter. Testa att uppdatera sidan.")
