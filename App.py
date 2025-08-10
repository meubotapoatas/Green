import os
import requests
import telebot
from datetime import datetime
from random import shuffle

# ===== VARIÁVEIS DE AMBIENTE =====
ODDS_API_KEY = os.getenv("ODDS_API_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
MIN_ODD = 1.8
MAX_PICKS_PER_DAY = 5

# ===== BOT TELEGRAM =====
bot = telebot.TeleBot(BOT_TOKEN)

# ===== BUSCAR ODDS E DADOS =====
def get_all_soccer_odds():
    url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals,spreads,btts&oddsFormat=decimal"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    return response.json()

# ===== ANALISAR E CRIAR PALPITES =====
def analyze_matches(data):
    picks = []
    for match in data:
        home = match["home_team"]
        away = match["away_team"]
        start_time = match["commence_time"]
        img_url = match.get("sport_nice", None)  # Algumas APIs fornecem imagem

        # Loop bookmakers
        for bookmaker in match.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    if outcome["price"] >= MIN_ODD:
                        prob = round((1 / outcome["price"]) * 100, 1)
                        picks.append({
                            "home": home,
                            "away": away,
                            "start_time": start_time,
                            "market": market["key"],
                            "bet": outcome["name"],
                            "odd": outcome["price"],
                            "prob": prob,
                            "img": img_url
                        })
    shuffle(picks)
    return picks[:MAX_PICKS_PER_DAY]

# ===== FORMATA MENSAGEM =====
def format_message(pick):
    time_str = datetime.fromisoformat(pick["start_time"].replace("Z", "+00:00")).strftime("%d/%m %H:%M")
    msg = f"🏟 **{pick['home']} vs {pick['away']}**\n"
    msg += f"🕒 {time_str}\n"
    msg += f"🎯 Mercado: {pick['market']}\n"
    msg += f"💡 Aposta: {pick['bet']} @ {pick['odd']}\n"
    msg += f"📈 Probabilidade estimada: {pick['prob']}%\n"
    msg += "────────────────────"
    return msg

# ===== COMANDOS TELEGRAM =====
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "🤖 Bot iniciado! Use /palpites para ver os jogos de hoje.")

@bot.message_handler(commands=["palpites"])
def send_palpites(message):
    data = get_all_soccer_odds()
    picks = analyze_matches(data)
    if not picks:
        bot.send_message(message.chat.id, "⚠️ Nenhum palpite encontrado no momento.")
        return
    for pick in picks:
        msg = format_message(pick)
        if pick["img"]:
            try:
                bot.send_photo(message.chat.id, pick["img"], caption=msg, parse_mode="Markdown")
            except:
                bot.send_message(message.chat.id, msg, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")

if __name__ == "__main__":
    print("✅ Bot rodando...")
    bot.polling()
