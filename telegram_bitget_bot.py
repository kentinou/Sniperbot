import os
import json
from flask import Flask, request
from python_bitget.rest.bitget_client import BitgetClient
from dotenv import load_dotenv
import telegram

load_dotenv()

app = Flask(__name__)

# Infos d'authentification
API_KEY = os.getenv("BITGET_API_KEY")
API_SECRET = os.getenv("BITGET_API_SECRET")
PASSPHRASE = os.getenv("BITGET_PASSPHRASE")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = BitgetClient(API_KEY, API_SECRET, PASSPHRASE)
bot = telegram.Bot(token=TG_TOKEN)

@app.route('/')
def home():
    return 'Bot actif !'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("📩 Webhook reçu:", data)

    symbol = data.get("symbol", "BTCUSDT")
    direction = data.get("signal", "buy")
    side = "open_long" if direction == "buy" else "open_short"

    # Envoi message Telegram
    bot.send_message(chat_id=TG_CHAT_ID, text=f"📈 Signal détecté : {direction.upper()} sur {symbol}")

    # Création de l’ordre sur Bitget
    try:
        result = client.mix_place_order(
            symbol=symbol,
            productType="umcbl",
            marginCoin="USDT",
            side="buy" if direction == "buy" else "sell",
            orderType="market",
            size="0.01",  # À ajuster selon ton capital
            price="",     # vide = market
        )
        print("✅ Réponse Bitget:", result)
        bot.send_message(chat_id=TG_CHAT_ID, text=f"✅ Trade exécuté : {direction.upper()} sur {symbol}")
    except Exception as e:
        print("❌ Erreur:", str(e))
        bot.send_message(chat_id=TG_CHAT_ID, text=f"❌ Erreur : {str(e)}")

    return '', 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
