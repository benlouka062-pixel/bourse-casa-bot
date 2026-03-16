import yfinance as yf
from datetime import datetime, time
import pytz
import json
import os
from cachetools import cached, TTLCache

# Cache 1 heure
cache = TTLCache(maxsize=100, ttl=3600)

MAROC_TZ = pytz.timezone('Africa/Casablanca')
ACTIONS = {
    "IAM": "IAM.CAS", "ATW": "ATW.CAS", "BCP": "BCP.CAS",
    "ADH": "ADH.CAS", "MNG": "MNG.CAS", "SMI": "SMI.CAS",
    "CMT": "CMT.CAS", "CIH": "CIH.CAS"
}

def is_market_open():
    """Retourne True si marché marocain ouvert (lundi-vendredi, 09:30–15:30)"""
    now = datetime.now(MAROC_TZ)
    if now.weekday() >= 5:  # samedi/dimanche
        return False
    market_open = time(9, 30)
    market_close = time(15, 30)
    return market_open <= now.time() <= market_close

@cached(cache)
def fetch_live_price(symbol, ticker):
    """Forcer yfinance avec suffixe .CAS, pas de simulation"""
    try:
        data = yf.download(ticker, period="1d", interval="1m", progress=False)
        if data.empty:
            # fallback sur le cache disque
            return load_cached_price(symbol)
        return round(data['Close'].iloc[-1], 2)
    except:
        return load_cached_price(symbol)

def load_cached_price(symbol):
    """Charge depuis le fichier cache JSON"""
    try:
        # Essayer d'abord le cache disque local
        if os.path.exists("data/prices.json"):
            with open("data/prices.json", "r") as f:
                cache_data = json.load(f)
                return cache_data.get(symbol, None)
        
        # Fallback GitHub Pages
        import requests
        url = "https://benlouka062-pixel.github.io/bourse-casa-bot./data.json"
        r = requests.get(url, timeout=5)
        data = r.json()
        for action in data.get('actions', []):
            if action.get('sym') == symbol:
                return action.get('prix')
    except:
        pass
    return None

def get_all_prices():
    """Point d'entrée principal : live si ouvert, cache sinon"""
    prices = {}
    for sym, ticker in ACTIONS.items():
        if is_market_open():
            prices[sym] = fetch_live_price(sym, ticker)
        else:
            prices[sym] = load_cached_price(sym)
    return prices
