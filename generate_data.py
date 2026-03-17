import requests
import json
import time
import os
from datetime import datetime

# === CONFIGURATION ===
BOT_TOKEN = "8342446918:AAG4cuQKWZypIeAmfTy45PB0r7hQ8QFjhqo"
CHAT_ID = "8150604747"
ALPHA_VANTAGE_KEY = "XC6GGBXO6U4RQTGR"  # TA CLÉ EXISTANTE

# === ACTIONS MAROCAINES (suffixe .CAS pour Alpha Vantage) ===
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
def get_price_from_alpha(symbol):
    """Récupère le dernier prix depuis Alpha Vantage"""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            return float(data["Global Quote"]["05. price"])
    except Exception as e:
        print(f"Erreur Alpha Vantage pour {symbol}: {e}")
    return None

def get_historique_from_alpha(symbol):
    """Récupère l'historique sur 30 jours"""
    try:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        
        if "Time Series (Daily)" in data:
            series = data["Time Series (Daily)"]
            # Trier par date et prendre les 30 derniers
            dates = sorted(series.keys(), reverse=True)[:30]
            return [float(series[d]["4. close"]) for d in dates]
    except Exception as e:
        print(f"Erreur historique {symbol}: {e}")
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
    """Récupère les métaux via GoldAPI (inchangé)"""
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
    
    # Métaux industriels (simulés)
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
    print("🔍 Récupération des données (Alpha Vantage)...")
    
    ancien_cache = lire_ancien_cache()
    anciennes_actions = {a['sym']: a for a in ancien_cache.get('actions', [])}
    
    actions_data = []
    source_globale = "📡 ALPHA VANTAGE"
    
    for sym, ticker in ACTIONS.items():
        print(f"  → {sym} ({ticker})...", end=" ")
        
        # Essayer de récupérer le prix
        prix = get_price_from_alpha(ticker)
        
        if prix:
            # Nouveau prix trouvé
            historique = get_historique_from_alpha(ticker)
            rsi = calculer_rsi(historique) if historique else 50
            
            # Support/résistance simplifiés
            support = round(prix * 0.97, 2)
            resistance = round(prix * 1.03, 2)
            
            # Signal
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
            # Pas de nouveau prix → on garde l'ancien cache
            if sym in anciennes_actions:
                ancien = anciennes_actions[sym].copy()
                ancien['source'] = "💾 CACHE"
                actions_data.append(ancien)
                print(f"💾 cache ({ancien.get('prix', '?')} DH)")
                source_globale = "💾 CACHE (marché fermé)"
            else:
                print("❌ aucune donnée")
        
        time.sleep(12)  # Respect des limites API Alpha Vantage (5 appels/min)
    
    # Métaux
    metaux = get_metaux_reels()
    
    output = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "source": source_globale,
        "masi": None,  # À ajouter plus tard
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
