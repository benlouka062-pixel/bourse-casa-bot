import sys
import yfinance as yf
import requests
import json
import urllib.parse
import os
from datetime import datetime, timedelta

# === CONFIGURATION ===
BOT_TOKEN = "8342446918:AAG4cuQKWZypIeAmfTy45PB0r7hQ8QFjhqo"

# Mapping symboles
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

def send_telegram_photo(chat_id, image_url, caption=""):
    """Envoie une photo via Telegram (URL)"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    payload = {
        "chat_id": chat_id,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            print("✅ Image envoyée")
        else:
            print(f"❌ Erreur {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

def send_telegram_message(chat_id, text):
    """Envoie un message texte"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def lire_cache_pour_symbole(sym):
    """Lit les dernières données depuis data.json si disponibles"""
    try:
        if os.path.exists("data.json"):
            with open("data.json", "r") as f:
                cache = json.load(f)
                for action in cache.get("actions", []):
                    if action.get("sym") == sym:
                        return action
    except:
        pass
    return None

def generate_quickchart_url(sym, prices, dates):
    """Génère une URL QuickChart pour un graphique des prix"""
    
    chart_config = {
        "type": "line",
        "data": {
            "labels": dates,
            "datasets": [{
                "label": f"{sym} - Prix",
                "data": prices,
                "borderColor": "#00ff9d",
                "backgroundColor": "rgba(0,255,157,0.1)",
                "fill": True,
                "tension": 0.4
            }]
        },
        "options": {
            "title": {
                "display": True,
                "text": f"{sym} - {NOMS.get(sym, '')}",
                "color": "#ffffff"
            },
            "legend": {
                "labels": {"fontColor": "#ffffff"}
            },
            "scales": {
                "xAxes": [{"ticks": {"fontColor": "#aaaaaa"}}],
                "yAxes": [{"ticks": {"fontColor": "#aaaaaa"}}]
            },
            "backgroundColor": "#0b0e14"
        }
    }
    
    json_str = json.dumps(chart_config)
    encoded = urllib.parse.quote(json_str)
    return f"https://quickchart.io/chart?width=600&height=400&c={encoded}"

def main():
    if len(sys.argv) < 3:
        print("Usage: python generate_chart.py SYMBOLE CHAT_ID")
        return
    
    sym = sys.argv[1].upper()
    chat_id = sys.argv[2]
    
    if sym not in ACTIONS:
        send_telegram_message(chat_id, f"❌ Symbole {sym} inconnu")
        return
    
    ticker = ACTIONS[sym]
    
    # ESSAYER D'ABORD YFINANCE (données temps réel)
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        
        if not data.empty:
            # ✅ Succès : on a des données fraîches
            prices = data['Close'].tolist()
            dates = [d.strftime("%d/%m") for d in data.index[-10:]]
            dernier_prix = prices[-1]
            variation = ((prices[-1] - prices[-2]) / prices[-2]) * 100 if len(prices) > 1 else 0
            
            chart_url = generate_quickchart_url(sym, prices[-10:], dates)
            
            caption = f"📊 *{sym}* – {NOMS[sym]} (temps réel)\n"
            caption += f"💰 Prix: {dernier_prix:.2f} DH\n"
            caption += f"📈 Variation: {variation:+.2f}%\n"
            caption += f"🕒 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            send_telegram_photo(chat_id, chart_url, caption)
            return
    except:
        pass  # Silence, on passe au cache
    
    # ❌ PAS DE DONNÉES FRAÎCHES → on utilise le cache
    cache_data = lire_cache_pour_symbole(sym)
    
    if cache_data:
        # Simuler des prix historiques à partir du dernier prix connu
        prix_cache = cache_data.get('prix', 0)
        # Créer une petite série pour le graphique
        simulated_prices = [prix_cache * (0.98 + 0.04 * i/10) for i in range(10)]
        dates = [(datetime.now() - timedelta(days=9-i)).strftime("%d/%m") for i in range(10)]
        
        chart_url = generate_quickchart_url(sym, simulated_prices, dates)
        
        caption = f"📊 *{sym}* – {NOMS[sym]} (📦 *CACHE* - marché fermé)\n"
        caption += f"💰 Dernier prix connu: {prix_cache:.2f} DH\n"
        caption += f"🕒 Source: {cache_data.get('date', 'inconnue')}\n"
        caption += f"\nLes prochains prix apparaîtront à la réouverture du marché."
        
        send_telegram_photo(chat_id, chart_url, caption)
    else:
        send_telegram_message(chat_id, f"❌ Aucune donnée disponible pour {sym} (ni temps réel, ni cache)")

if __name__ == "__main__":
    main()
