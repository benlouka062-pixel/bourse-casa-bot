import yfinance as yf
import json
import time
import os
from datetime import datetime

# === TES VRAIS TOKENS ===
BOT_TOKEN = "8342446918:AAG4cuQKWZypIeAmfTy45PB0r7hQ8QFjhqo"
CHAT_ID = "8150604747"

# Actions à suivre
ACTIONS = {
    "ADH": "ADH.MS", "DHO": "DHO.MS", "ENL": "ENL.MS", "IAM": "IAM.MS",
    "AGZ": "AGZ.MS", "TQM": "TQM.MS", "ATW": "ATW.MS", "BCP": "BCP.MS",
    "CIH": "CIH.MS", "MNG": "MNG.MS", "SMI": "SMI.MS", "CMT": "CMT.MS"
}

NOMS = {
    "ADH": "ADDOHA", "DHO": "DELTA HOLDING", "ENL": "ENNAKL", "IAM": "ITISSALAT",
    "AGZ": "AFRIQUIA GAZ", "TQM": "TAQA MOROCCO", "ATW": "ATTIJARI", "BCP": "BCP",
    "CIH": "CIH", "MNG": "MANAGEM", "SMI": "SMI", "CMT": "CMT"
}

# === FONCTIONS EXISTANTES ===
def calculer_rsi(prix_historique):
    """Calcule le RSI à partir d'une liste de prix"""
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

# === NOUVELLES FONCTIONS POUR SUPPORTS/RÉSISTANCES ===
def calculer_support_resistance(prix_historique, periode=20):
    """
    Calcule les niveaux de support et résistance dynamiques
    Support = plus bas sur la période
    Résistance = plus haut sur la période
    """
    if len(prix_historique) < periode:
        return None, None
    
    support = min(prix_historique[-periode:])
    resistance = max(prix_historique[-periode:])
    
    return round(support, 2), round(resistance, 2)

def distance_vers_niveau(prix, niveau):
    """Calcule la distance en pourcentage par rapport à un niveau"""
    if not prix or not niveau:
        return None
    return round(((prix - niveau) / niveau) * 100, 1)

def get_price_and_rsi(sym, ticker):
    """Récupère le prix, calcule RSI ET support/résistance"""
    try:
        hist = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if hist.empty:
            return None
        
        prix = round(hist['Close'].iloc[-1], 2)
        prix_list = hist['Close'].tolist()
        rsi = calculer_rsi(prix_list)
        
        # === NOUVEAU : calcul support/résistance ===
        support, resistance = calculer_support_resistance(prix_list)
        dist_support = distance_vers_niveau(prix, support)
        dist_resistance = distance_vers_niveau(prix, resistance)
        
        # Signal
        if rsi < 30:
            signal = "ACHAT"
        elif rsi > 70:
            signal = "VENTE"
        else:
            signal = "ATTENTE"
        
        return {
            "sym": sym,
            "nom": NOMS[sym],
            "prix": prix,
            "rsi": rsi,
            "signal": signal,
            # === NOUVEAU ===
            "support": support,
            "resistance": resistance,
            "dist_support": dist_support,
            "dist_resistance": dist_resistance
        }
    except Exception as e:
        print(f"Erreur {sym}: {e}")
        return None

def get_masi():
    """Récupère l'indice MASI"""
    try:
        masi = yf.download("^MASI", period="1d", progress=False)
        if not masi.empty:
            return round(masi['Close'].iloc[-1], 2)
    except:
        pass
    return None

def lire_ancien_cache():
    """Lit l'ancien fichier data.json s'il existe"""
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return {"actions": []}

def main():
    print("🔍 Récupération des données...")
    
    # Lire l'ancien cache
    ancien_cache = lire_ancien_cache()
    anciennes_actions = {a['sym']: a for a in ancien_cache.get('actions', [])}
    
    actions_data = []
    source_globale = "📡 TEMPS RÉEL"
    
    for sym, ticker in ACTIONS.items():
        nouveau = get_price_and_rsi(sym, ticker)
        if nouveau:
            actions_data.append(nouveau)
            print(f"✅ {sym}: nouveau prix récupéré (support: {nouveau['support']}, résistance: {nouveau['resistance']})")
        else:
            # Pas de nouveau prix → on garde l'ancien s'il existe
            if sym in anciennes_actions:
                ancien = anciennes_actions[sym].copy()
                ancien['source'] = "💾 CACHE"
                actions_data.append(ancien)
                print(f"💾 {sym}: ancien prix conservé ({ancien.get('prix', '?')} DH)")
                source_globale = "💾 CACHE (hors séance)"
            else:
                print(f"❌ {sym}: aucune donnée (neuf ni cache)")
        time.sleep(1)
    
    masi = get_masi()
    if not masi and ancien_cache.get('masi'):
        masi = ancien_cache['masi']
    
    # Structure finale
    output = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "source": source_globale,
        "masi": masi,
        "volume": "N/A",
        "variation": "N/A",
        "actions": actions_data
    }
    
    # Sauvegarde
    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Fichier data.json généré avec {len(actions_data)} actions")
    print(f"📦 Source: {source_globale}")

if __name__ == "__main__":
    main()
