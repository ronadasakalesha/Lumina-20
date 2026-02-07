from src.data_fetcher import fetch_candles
from src.indicators import calculate_ema
from src.strategy import apply_strategy
from src.telegram_utils import send_telegram_message, format_signal_message
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

def run_bot_cycle():
    """
    Run one cycle of the bot: Fetch data -> Calculate Indicators -> Check Signals -> Alert.
    """
    symbol = "BTCUSD"
    interval = "15m"  # 15 minutes
    
    # Calculate start and end times
    # We need enough history for EMA 20 + Strategy Lookback (at least 50 candles)
    # 50 candles * 15m = 750m = 12.55 hours. Let's fetch 2 days just to be safe.
    end_time = int(datetime.now().timestamp())
    start_time = int((datetime.now() - timedelta(days=2)).timestamp())
    
    # print(f"[{datetime.now()}] Fetching data...")
    df = fetch_candles(symbol, interval, start=start_time, end=end_time)
    
    if df.empty:
        print("Failed to fetch data.")
        return

    # Calculate EMA
    df = calculate_ema(df, period=20)
    
    # Apply Strategy
    df = apply_strategy(df)
    
    # Check the LAST COMPLETED candle for a Signal
    # The last row in df might be the currently forming candle depending on API.
    # Delta API typically returns closed candles in history, but we should verify.
    # Assuming the last row is the latest closed candle or the current forming one.
    # Strategy logic iterates up to len(df)-2.
    # Signals are marked on the candle where the ENTRY condition is met.
    
    # Let's check the last few candles for a NEW signal
    # We only want to alert if a signal was triggered VERY RECENTLY.
    # e.g., in the last closed candle.
    
    latest_candles = df.tail(5) # Check last 5 candles
    
    # Check for Entry Signals
    new_signals = latest_candles[latest_candles['entry_signal'] != 0]
    
    if not new_signals.empty:
        for index, row in new_signals.iterrows():
            # Check if this signal is "fresh" (e.g. within current cycle window)
            # For now, we print it. In a real loop, we would track "last_alerted_time" to avoid duplicates.
            
            # Simple deduplication logic could be added here
            msg = format_signal_message(row)
            print(f"\n!!! SIGNAL DETECTED !!!\n{msg}\n")
            
            # Send Telegram Alert
            # send_telegram_message(msg) 
            # Uncomment above to enable live alerts. For this script run, we just print.
            
            return row # Return signal found
            
    # print("No new signals.")
    return None

def main():
    print("✨ Starting Lumina 20 Strategy Bot...")
    print("Checking for existing signals in recent data...")
    
    # Run one cycle immediately
    signal = run_bot_cycle()
    
    if signal is not None:
         print("Signal found in recent data (see above).")
         # Optionally send alert here if user wants immediate alert on run
         # msg = format_signal_message(signal)
         # send_telegram_message(msg)
    else:
        print("No active signals in the immediate past.")
        
if __name__ == "__main__":
    main()
