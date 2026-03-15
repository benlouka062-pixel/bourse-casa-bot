import requests

BOT_TOKEN = "8342446918:AAG4cuQKWZypIeAmfTy45PB0r7hQ8QFjhqo"

# URL de ton webhook (à remplacer par ton URL GitHub Pages plus tard)
# Pour l'instant, on utilise un placeholder
WEBHOOK_URL = "https://benlouka062-pixel.github.io/bourse-casa-bot/webhook"

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    payload = {"url": WEBHOOK_URL}
    
    try:
        r = requests.post(url, json=payload)
        if r.status_code == 200:
            print("✅ Webhook configuré avec succès")
            print(r.json())
        else:
            print(f"❌ Erreur {r.status_code}: {r.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    set_webhook()
