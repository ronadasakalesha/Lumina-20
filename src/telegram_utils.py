import requests
from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(message):
    """
    Send a message to a Telegram user or group using a bot.

    Args:
        message (str): The text message to send.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram credentials missing in config.py")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        # print("Telegram alert sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Telegram alert: {e}")

def format_signal_message(signal_row):
    """
    Format the signal row into the specified string format.
    
    Time: 2026-02-07 03:00 UTC
    Type: BUY
    Entry: 70597.0
    SL: 70307.0
    TP: 71757.0 (1:4 Risk-Reward)
    """
    type_str = "BUY" if signal_row['entry_signal'] == 1 else "SELL"
    # Format time explicitly if it's a pandas timestamp
    time_str = str(signal_row['time']) 
    
    message = (
        f"Time: {time_str} UTC\n"
        f"Type: {type_str}\n"
        f"Entry: {signal_row['entry_price']}\n"
        f"SL: {signal_row['stop_loss']}\n"
        f"TP: {signal_row['take_profit']} (1:4 Risk-Reward)"
    )
    return message
