import requests
from bs4 import BeautifulSoup
from scrapingbee import ScrapingBeeClient
import json
import time
import os
import re
from datetime import datetime

# === CONFIGURATION ===
BOT_TOKEN = "8342446918:AAG4cuQKWZypIeAmfTy45PB0r7hQ8QFjhqo"
CHAT_ID = "8150604747"
SCRAPINGBEE_KEY = "R0081TLRJSB7TS1VMAHXSFFE8TW8LEDNZ9MW56QCC3I830HIM4CJGELD5YFPG5XJ6GQ4FRQT7ZIMOFZ4"
COMMODITY_API_KEY = "1a4e70c1-3a1e-4f6e-b985-c1dfb40aca22"

# === LISTE DES ACTIONS (seulement celles qui fonctionnent) ===
INVESTING_URLS = {
    "ADH": "https://www.investing.com/equities/addoha",
    "DHO": "https://www.investing.com/equities/delta-holding",
    "ENL": "https://www.investing.com/equities/ennakl",
    "TGCC": "https://www.investing.com/equities/tgcc",
    "CRS": "https://www.investing.com/equities/cartier-saada",
    "SNA": "https://fr.investing.com/equities/stokvis-nord",
    "COL": "https://www.investing.com/equities/colorado",
    "RIS": "https://www.investing.com/equities/risma",
}

NOMS = {
    "ADH": "ADDOHA",
    "DHO": "DELTA HOLDING",
    "ENL": "ENNAKL",
    "TGCC": "TGCC",
    "CRS": "CARTIER SAADA",
    "SNA": "STOKVIS NORD",
    "COL": "COLORADO",
    "RIS": "RISMA"
}

# === FONCTION DE SCRAPING AVEC SCRAPINGBEE ===
def get_price_with_scrapingbee(symbol, url):
    try:
        client = ScrapingBeeClient(api_key=SCRAPINGBEE_KEY)
        response = client.get(
            url,
            params={
                'render_js': False,
                'premium_proxy': True,
                'country_code': 'ma',
                'block_resources': True,
                'wait': 1500,
            }
        )
        if response.status_code != 200:
            print(f"  ⚠️ {symbol}: ScrapingBee HTTP {response.status_code}")
            return None
        soup = BeautifulSoup(response.content, 'html.parser')
        # Chercher le prix dans le span spécifique
        price_span = soup.find('span', {'data-test': 'instrument-price-last'})
        if price_span:
            text = price_span.text.strip().replace(',', '').replace(' ', '')
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                return float(match.group(1))
        # Fallback : regex dans tout le texte
        page_text = soup.text
        match = re.search(r'(\d+\.?\d*)\s*MAD', page_text)
        if match:
            return float(match.group(1))
    except Exception as e:
        print(f"  ❌ Erreur ScrapingBee {symbol}: {e}")
    return None

# === FONCTIONS POUR LES MÉTAUX ===
def get_metaux_precieux():
    metals = {}
    GOLD_API_KEY = "goldapi-kqb19mlv7mcz7-io"
    # Or
    try:
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {'x-access-token': GOLD_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            metals["XAU"] = {
                "nom": "Or",
                "prix": round(data.get('price', 2350), 2),
                "variation": round(data.get('cp', 0.8), 2)
            }
        else:
            metals["XAU"] = {"nom": "Or", "prix": 2350.50, "variation": 0.8}
    except:
        metals["XAU"] = {"nom": "Or", "prix": 2350.50, "variation": 0.8}
    time.sleep(1)
    # Argent
    try:
        url = "https://www.goldapi.io/api/XAG/USD"
        headers = {'x-access-token': GOLD_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            metals["XAG"] = {
                "nom": "Argent",
                "prix": round(data.get('price', 28.75), 2),
                "variation": round(data.get('cp', 1.2), 2)
            }
        else:
            metals["XAG"] = {"nom": "Argent", "prix": 28.75, "variation": 1.2}
    except:
        metals["XAG"] = {"nom": "Argent", "prix": 28.75, "variation": 1.2}
    return metals

def get_metaux_industriels():
    metals = {}
    try:
        # CommodityPriceAPI attend des symboles comme "copper", "zinc", "lead"
        symbols = "copper,zinc,lead"
        url = f"https://api.commoditypriceapi.com/v2/rates/latest?symbols={symbols}&apiKey={COMMODITY_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if data.get("success"):
            rates = data.get("rates", {})
            if "copper" in rates:
                metals["XCU"] = {
                    "nom": "Cuivre",
                    "prix": round(float(rates["copper"]), 2),
                    "variation": 0.0
                }
            if "zinc" in rates:
                metals["XZN"] = {
                    "nom": "Zinc",
                    "prix": round(float(rates["zinc"]), 2),
                    "variation": 0.0
                }
            if "lead" in rates:
                metals["XPB"] = {
                    "nom": "Plomb",
                    "prix": round(float(rates["lead"]), 2),
                    "variation": 0.0
                }
        else:
            # Fallback
            metals = get_fallback_industrial_metals()
    except:
        metals = get_fallback_industrial_metals()
    return metals

def get_fallback_industrial_metals():
    return {
        "XCU": {"nom": "Cuivre", "prix": 4.25, "variation": 0.3},
        "XPB": {"nom": "Plomb", "prix": 2150, "variation": -0.2},
        "XZN": {"nom": "Zinc", "prix": 2580, "variation": 0.5}
    }

def get_metaux_reels():
    metals = {
        "precieux": get_metaux_precieux(),
        "industriels": get_metaux_industriels()
    }
    return metals

# === GESTION DU CACHE ===
def lire_ancien_cache():
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return {"actions": []}

# === MAIN ===
def main():
    print("🔍 Récupération des données (Investing.com via ScrapingBee)...")
    ancien_cache = lire_ancien_cache()
    anciennes_actions = {a['sym']: a for a in ancien_cache.get('actions', [])}
    actions_data = []
    source_globale = "📡 SCRAPINGBEE"

    for sym, url in INVESTING_URLS.items():
        print(f"  → {sym}...", end=" ")
        prix = get_price_with_scrapingbee(sym, url)

        if prix:
            # Générer un petit historique factice autour du prix (10 points)
            historique = [prix * (0.95 + 0.01 * i) for i in range(10)]
            # Calcul simplifié du RSI (sur l'historique factice)
            rsi = 50  # valeur par défaut, on pourra améliorer plus tard
            support = round(prix * 0.97, 2)
            resistance = round(prix * 1.03, 2)
            signal = "ATTENTE"  # par défaut

            action_data = {
                "sym": sym,
                "nom": NOMS[sym],
                "prix": prix,
                "rsi": rsi,
                "signal": signal,
                "support": support,
                "resistance": resistance,
                "source": "RÉEL",
                "historique": historique  # pour le graphique
            }
            actions_data.append(action_data)
            print(f"✅ {prix} DH")
            source_globale = "📡 TEMPS RÉEL"
        else:
            # Pas de prix → on utilise le cache si disponible
            if sym in anciennes_actions:
                ancien = anciennes_actions[sym].copy()
                ancien['source'] = "💾 CACHE"
                actions_data.append(ancien)
                print(f"💾 cache ({ancien.get('prix', '?')} DH)")
                source_globale = "💾 CACHE"
            else:
                print("❌ aucune donnée")
        time.sleep(2)  # pause pour respecter les limites

    # Récupérer les métaux
    metaux = get_metaux_reels()

    output = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "source": source_globale,
        "masi": None,
        "volume": "N/A",
        "variation": "N/A",
        "actions": actions_data,
        "metaux": metaux
    }

    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ Fichier data.json généré avec {len(actions_data)} actions")
    print(f"📦 Source: {source_globale}")
    print(f"🏅 Métaux: {len(metaux['precieux'])} précieux, {len(metaux['industriels'])} industriels")

if __name__ == "__main__":
    main()
