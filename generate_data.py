import yfinance as yf
import requests
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

def calculer_support_resistance(prix_historique, periode=20):
    if len(prix_historique) < periode:
        return None, None
    support = min(prix_historique[-periode:])
    resistance = max(prix_historique[-periode:])
    return round(support, 2), round(resistance, 2)

def distance_vers_niveau(prix, niveau):
    if not prix or not niveau:
        return None
    return round(((prix - niveau) / niveau) * 100, 1)

def detecter_breakout(prix_actuel, resistance, volume_actuel, volume_moyen, seuil_volume=1.5):
    if not prix_actuel or not resistance or not volume_actuel or not volume_moyen:
        return None
    if prix_actuel > resistance and volume_actuel > volume_moyen * seuil_volume:
        return {
            "type": "BREAKOUT_HAUSSIER",
            "prix": prix_actuel,
            "niveau": resistance,
            "volume_ratio": round(volume_actuel / volume_moyen, 2)
        }
    return None

def get_volume_data(ticker):
    try:
        data = yf.download(ticker, period="5d", interval="1d", progress=False)
        if len(data) >= 5:
            volumes = data['Volume'].tolist()
            volume_actuel = volumes[-1]
            volume_moyen = sum(volumes[-5:-1]) / 4 if len(volumes) > 1 else volume_actuel
            return volume_actuel, volume_moyen
    except:
        pass
    return None, None

def detecter_divergence(prix_historique, rsi_historique, periode=14):
    if len(prix_historique) < periode * 2 or len(rsi_historique) < periode * 2:
        return None
    prix_recents = prix_historique[-periode:]
    rsi_recents = rsi_historique[-periode:]
    prix_prec = prix_historique[-periode*2:-periode]
    rsi_prec = rsi_historique[-periode*2:-periode]
    if min(prix_recents) < min(prix_prec) and min(rsi_recents) > min(rsi_prec):
        return {"type": "DIVERGENCE_HAUSSIERE", "message": "📈 Prix plus bas, RSI plus haut → retournement haussier possible"}
    if max(prix_recents) > max(prix_prec) and max(rsi_recents) < max(rsi_prec):
        return {"type": "DIVERGENCE_BAISSIERE", "message": "📉 Prix plus haut, RSI plus bas → retournement baissier possible"}
    return None

def calculer_rsi_historique(prix_historique):
    rsi_historique = []
    for i in range(len(prix_historique)):
        if i < 14:
            rsi_historique.append(50)
        else:
            rsi_historique.append(calculer_rsi(prix_historique[:i+1]))
    return rsi_historique

# === NOUVELLE FONCTION : ALERTES CONDITIONNELLES ===
def verifier_alertes(actions_data):
    """Vérifie les conditions d'alerte et retourne les messages"""
    alertes = []
    
    # === SEUILS PERSONNALISABLES (modifie ici tes conditions) ===
    SEUILS = {
        "IAM": {
            "prix_max": 150,        # Alerte si IAM > 150 DH
            "prix_min": 140,        # Alerte si IAM < 140 DH
            "rsi_min": 30,           # Alerte si RSI < 30
            "rsi_max": 70            # Alerte si RSI > 70
        },
        "ADH": {
            "prix_min": 24,          # Alerte si ADH < 24 DH
            "rsi_max": 70            # Alerte si RSI > 70
        },
        "MNG": {
            "prix_max": 2000,        # Alerte si MNG > 2000 DH
            "rsi_min": 30            # Alerte si RSI < 30
        },
        "ATW": {
            "prix_max": 460,         # Alerte si ATW > 460 DH
            "prix_min": 440          # Alerte si ATW < 440 DH
        }
        # Ajoute d'autres actions ici
    }
    
    for action in actions_data:
        sym = action["sym"]
        prix = action.get("prix")
        rsi = action.get("rsi")
        
        if sym in SEUILS:
            seuil = SEUILS[sym]
            
            # Alerte prix maximum
            if "prix_max" in seuil and prix and prix > seuil["prix_max"]:
                alertes.append(f"🚨 *{sym}* a dépassé {seuil['prix_max']} DH (actuel: {prix} DH)")
            
            # Alerte prix minimum
            if "prix_min" in seuil and prix and prix < seuil["prix_min"]:
                alertes.append(f"🚨 *{sym}* est passé sous {seuil['prix_min']} DH (actuel: {prix} DH)")
            
            # Alerte RSI survendu
            if "rsi_min" in seuil and rsi and rsi < seuil["rsi_min"]:
                alertes.append(f"📉 *{sym}* RSI survendu: {rsi} (seuil: {seuil['rsi_min']})")
            
            # Alerte RSI surachat
            if "rsi_max" in seuil and rsi and rsi > seuil["rsi_max"]:
                alertes.append(f"📈 *{sym}* RSI surachat: {rsi} (seuil: {seuil['rsi_max']})")
    
    return alertes

def send_telegram_message(chat_id, text):
    """Envoie un message Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except:
        pass

def get_price_and_rsi(sym, ticker):
    try:
        hist = yf.download(ticker, period="2mo", interval="1d", progress=False)
        if hist.empty:
            return None
        
        prix = round(hist['Close'].iloc[-1], 2)
        prix_list = hist['Close'].tolist()
        rsi_historique = calculer_rsi_historique(prix_list)
        rsi_actuel = rsi_historique[-1]
        
        support, resistance = calculer_support_resistance(prix_list)
        dist_support = distance_vers_niveau(prix, support)
        dist_resistance = distance_vers_niveau(prix, resistance)
        
        volume_actuel, volume_moyen = get_volume_data(ticker)
        breakout = detecter_breakout(prix, resistance, volume_actuel, volume_moyen)
        divergence = detecter_divergence(prix_list, rsi_historique)
        
        if breakout:
            signal = "BREAKOUT"
        elif divergence:
            signal = "DIVERGENCE"
        elif rsi_actuel < 30:
            signal = "ACHAT"
        elif rsi_actuel > 70:
            signal = "VENTE"
        else:
            signal = "ATTENTE"
        
        result = {
            "sym": sym,
            "nom": NOMS[sym],
            "prix": prix,
            "rsi": rsi_actuel,
            "signal": signal,
            "support": support,
            "resistance": resistance,
            "dist_support": dist_support,
            "dist_resistance": dist_resistance
        }
        
        if breakout:
            result["breakout"] = breakout
        if divergence:
            result["divergence"] = divergence
        
        return result
    except Exception as e:
        print(f"Erreur {sym}: {e}")
        return None

def get_masi():
    try:
        masi = yf.download("^MASI", period="1d", progress=False)
        if not masi.empty:
            return round(masi['Close'].iloc[-1], 2)
    except:
        pass
    return None

def lire_ancien_cache():
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            return json.load(f)
    return {"actions": []}

def main():
    print("🔍 Récupération des données...")
    
    ancien_cache = lire_ancien_cache()
    anciennes_actions = {a['sym']: a for a in ancien_cache.get('actions', [])}
    
    actions_data = []
    source_globale = "📡 TEMPS RÉEL"
    
    for sym, ticker in ACTIONS.items():
        nouveau = get_price_and_rsi(sym, ticker)
        if nouveau:
            actions_data.append(nouveau)
            if nouveau.get('breakout'):
                print(f"🚀 {sym}: BREAKOUT détecté !")
            elif nouveau.get('divergence'):
                print(f"📊 {sym}: {nouveau['divergence']['message']}")
            else:
                print(f"✅ {sym}: nouveau prix récupéré")
        else:
            if sym in anciennes_actions:
                ancien = anciennes_actions[sym].copy()
                ancien['source'] = "💾 CACHE"
                actions_data.append(ancien)
                print(f"💾 {sym}: ancien prix conservé ({ancien.get('prix', '?')} DH)")
                source_globale = "💾 CACHE (hors séance)"
            else:
                print(f"❌ {sym}: aucune donnée")
        time.sleep(1)
    
    masi = get_masi()
    if not masi and ancien_cache.get('masi'):
        masi = ancien_cache['masi']
    
    # === NOUVEAU : Vérification des alertes ===
    alertes = verifier_alertes(actions_data)
    if alertes:
        message_alertes = "🚨 *ALERTES ACTIONS*\n\n" + "\n".join(alertes)
        send_telegram_message(CHAT_ID, message_alertes)
        print(f"📢 {len(alertes)} alerte(s) envoyée(s)")
    
    # Structure finale
    output = {
        "date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "source": source_globale,
        "masi": masi,
        "volume": "N/A",
        "variation": "N/A",
        "actions": actions_data
    }
    
    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Fichier data.json généré avec {len(actions_data)} actions")
    print(f"📦 Source: {source_globale}")

if __name__ == "__main__":
    main()
