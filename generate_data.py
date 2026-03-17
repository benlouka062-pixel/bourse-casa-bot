import requests
import json
import time
import os
from datetime import datetime

# === CONFIGURATION ===
BOT_TOKEN = "8342446918:AAG4cuQKWZypIeAmfTy45PB0r7hQ8QFjhqo"
CHAT_ID = "8150604747"
TWELVE_DATA_KEY = "c2449bacc81b426884c2ab2a69c21df3"  # TA CLÉ

# === ACTIONS MAROCAINES (suffixe .CAS pour Twelve Data) ===
ACTIONS = {
    "ADH": "ADH.CAS", "DHO": "DHO.CAS", "ENL": "ENL.CAS", "IAM": "IAM.CAS",
    "AGZ": "AGZ.CAS", "TQM": "TQM.CAS", "ATW": "ATW.CAS", "BCP": "BCP.CAS",
    "CIH": "CIH.CAS", "MNG": "MNG.CAS", "SMI": "SMI.CAS", "CMT": "CMT.CAS"
}

NOMS = {
    "ADH": "ADDOHA", "DHO": "DELTA HOLDING", "ENL": "ENNAKL", "IAM": "ITISSALAT",
    "AGZ": "AFRIQUIA GAZ", "TQM": "TAQA MOROCCO", "ATW": "ATTIJARI", "BCP": "BCP",
    "CIH": "CIH", "MNG": "MANAGEM", "SMI": "SMI", "CMT": "CMT"
}

# === FONCTIONS ===
def get_price_from_twelve(symbol):
    """Récupère le dernier prix depuis Twelve Data"""
    try:
        url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_DATA_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if "price" in data:
            return float(data["price"])
        else:
            print(f"  ⚠️ Twelve Data: {data.get('message', 'pas de prix')}")
    except Exception as e:
        print(f"  ❌ Erreur Twelve Data: {e}")
    return None

def get_historique_from_twelve(symbol):
    """Récupère l'historique sur 30 jours"""
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1day&outputsize=30&apikey={TWELVE_DATA_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if "values" in data:
            return [float(v["close"]) for v in data["values"]]
    except:
        pass
    return []

def calculer_rsi(prix_historique):
    """RSI simplifié"""
    if len(prix_historique) < 15:
        return 50
    gains = 0
    pertes = 0
    for i in range(1, 15):
        diff = prix_historique[-i] - prix_historique[-i-1]
        if diff > 0:
            gains += diff
        else:
            pertes += abs(diff)
    if pertes == 0:
        return 100
    rs = gains / pertes
    return round(100 - (100 / (1 + rs)), 1)

def get_metaux_reels():
    """GoldAPI (inchangé)"""
    metals = {"precieux": {}, "industriels": {}}
    GOLD_API_KEY = "goldapi-kqb19mlv7mcz7-io"
    
    # Or
    try:
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {'x-access-token': GOLD_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            metals["precieux"]["XAU"] = {
                "nom": "Or", "prix": round(data.get('price', 2350), 2),
                "variation": round(data.get('cp', 0.8), 2)
            }
    except:
        metals["precieux"]["XAU"] = {"nom": "Or", "prix": 2350.50, "variation": 0.8}
    
    time.sleep(1)
    
    # Argent
    try:
        url = "https://www.goldapi.io/api/XAG/USD"
        headers = {'x-access-token': GOLD_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            metals["precieux"]["XAG"] = {
                "nom": "Argent", "prix": round(data.get('price', 28.75), 2),
                "variation": round(data.get('cp', 1.2), 2)
            }
    except:
        metals["precieux"]["XAG"] = {"nom": "Argent", "prix": 28.75, "variation": 1.2}
    
    # Métaux industriels
    metals["industriels"] = {
        "XCU": {"nom": "Cuivre", "prix": 4.25, "variation": 0.3},
        "XPB": {"nom": "Plomb", "prix": 2150, "variation": -0.2},
        "XZN": {"nom": "Zinc", "prix": 2580, "variation": 0.5}
    }
    return metals

def lire_ancien_cache():
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return {"actions": []}

def main():
    print("🔍 Récupération des données (Twelve Data)...")
    
    ancien_cache = lire_ancien_cache()
    anciennes_actions = {a['sym']: a for a in ancien_cache.get('actions', [])}
    
    actions_data = []
    source_globale = "📡 TWELVE DATA"
    
    for sym, ticker in ACTIONS.items():
        print(f"  → {sym} ({ticker})...", end=" ")
        
        # Essayer Twelve Data
        prix = get_price_from_twelve(ticker)
        
        if prix:
            # Nouveau prix trouvé
            historique = get_historique_from_twelve(ticker)
            rsi = calculer_rsi(historique) if historique else 50
            
            support = round(prix * 0.97, 2)
            resistance = round(prix * 1.03, 2)
            
            if rsi < 30:
                signal = "ACHAT"
            elif rsi > 70:
                signal = "VENTE"
            else:
                signal = "ATTENTE"
            
            action_data = {
                "sym": sym,
                "nom": NOMS[sym],
                "prix": prix,
                "rsi": rsi,
                "signal": signal,
                "support": support,
                "resistance": resistance,
                "source": "RÉEL",
                "historique": historique[-10:] if historique else []
            }
            actions_data.append(action_data)
            print(f"✅ {prix} DH")
            source_globale = "📡 TEMPS RÉEL"
        else:
            # Pas de prix → cache
            if sym in anciennes_actions:
                ancien = anciennes_actions[sym].copy()
                ancien['source'] = "💾 CACHE"
                actions_data.append(ancien)
                print(f"💾 cache ({ancien.get('prix', '?')} DH)")
                source_globale = "💾 CACHE"
            else:
                print("❌ aucune donnée")
        
        time.sleep(1)  # Politesse
    
    # Métaux
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

if __name__ == "__main__":
    main()
