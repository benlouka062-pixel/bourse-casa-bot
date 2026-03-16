import requests
from cachetools import cached, TTLCache

GOLD_API_KEY = "goldapi-kqb19mlv7mcz7-io"
cache_gold = TTLCache(maxsize=10, ttl=300)  # 5 minutes

@cached(cache_gold)
def get_gold_price():
    """Récupère le prix de l'or en USD"""
    try:
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {'x-access-token': GOLD_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return round(data['price'], 2), round(data['cp'], 2)
        else:
            # Fallback valeurs par défaut
            return 2350.50, 0.8
    except:
        return 2350.50, 0.8

@cached(cache_gold)
def get_silver_price():
    """Récupère le prix de l'argent en USD"""
    try:
        url = "https://www.goldapi.io/api/XAG/USD"
        headers = {'x-access-token': GOLD_API_KEY}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return round(data['price'], 2), round(data['cp'], 2)
        else:
            return 28.75, 1.2
    except:
        return 28.75, 1.2
