from src.telegram_utils import send_telegram_message

if __name__ == "__main__":
    message = "🔔 EMA 20 Strategy Bot: Telegram Integration Verified!"
    print(f"Sending test message: {message}")
    send_telegram_message(message)
    print("Check your Telegram for the message.")
