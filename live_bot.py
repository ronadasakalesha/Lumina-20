from src.data_fetcher import fetch_candles
from src.indicators import calculate_ema
from src.strategy import apply_strategy
from src.telegram_utils import send_telegram_message, format_signal_message
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
from src.config import TICKERS

def get_seconds_to_next_candle(interval_minutes=15, buffer_seconds=10):
    """
    Calculate seconds to sleep until the next candle close + buffer.
    """
    now = datetime.now()
    # Calculate next interval time
    next_minute = (now.minute // interval_minutes + 1) * interval_minutes
    next_run_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=next_minute)
    
    # If next_minute is 60, it handles hour rollover automatically via timedelta
    
    seconds_to_wait = (next_run_time - now).total_seconds() + buffer_seconds
    return seconds_to_wait

def run_live_bot():
    print("✨ Starting Lumina 20 Strategy Bot (Candle Close Mode)...")
    print("Press Ctrl+C to stop.")
    
    last_processed_time = None
    buffer_seconds = 10 # Buffer for broker data update
    
    while True:
        try:
            # 1. Calculate wait time
            wait_seconds = get_seconds_to_next_candle(15, buffer_seconds)
            next_run_str = (datetime.now() + timedelta(seconds=wait_seconds)).strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Waiting {int(wait_seconds)}s for next candle close... (Next run: {next_run_str})")
            
            time.sleep(wait_seconds)
            
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Executing Strategy Check...")
            
            # 2. Fetch recent data
            # End time is current timestamp. 
            # fetch_candles logic should inherently handle closed candles if we ask for end=now? 
            # Actually, Delta API 'end' is exclusive usually. 
            # If we run at 10:15:10, we want data up to 10:15:00.
            
            end_time = int(datetime.now().timestamp())
            start_time = int((datetime.now() - timedelta(days=2)).timestamp())
            
            for symbol in TICKERS:
                # print(f"Checking {symbol}...")
                df = fetch_candles(symbol, "15m", start=start_time, end=end_time)
                
                if not df.empty:
                    # 2. Calculate Indicators
                    df = calculate_ema(df, period=20)
                    
                    # 3. Apply Strategy
                    df = apply_strategy(df)
                    
                    # 4. Check for *NEW* signals
                    signals = df[df['entry_signal'] != 0]
                    
                    if not signals.empty:
                        last_signal = signals.iloc[-1]
                        signal_time = last_signal['time']
                        
                        # Unique key for tracking: Symbol + Time
                        signal_key = f"{symbol}_{signal_time}"
                        
                        # If this is a new signal we haven't processed yet
                        if last_processed_times[symbol] is None or signal_time > last_processed_times[symbol]:
                            
                            # Check if signal is FRESH (within last 30 mins)
                            # This prevents alerting old signals on bot restart
                            signal_timestamp = pd.to_datetime(signal_time)
                            if (datetime.now() - signal_timestamp).total_seconds() < 1800: # 30 mins
                                print(f"\n🔥 NEW {symbol} SIGNAL DETECTED at {signal_time} 🔥")
                                
                                # Add Symbol to message
                                msg = f"Symbol: {symbol}\n" + format_signal_message(last_signal)
                                print(msg)
                                send_telegram_message(msg)
                            else:
                                print(f"Found signal for {symbol} at {signal_time}, but it's old (stale). Skipping alert.")
                            
                            last_processed_times[symbol] = signal_time
                        else:
                             pass # Old signal already processed
                
                if not signals.empty:
                    # Get the very last signal
                    last_signal = signals.iloc[-1]
                    signal_time = last_signal['time']
                    
                    # If this is a new signal we haven't processed yet
                    if last_processed_time is None or signal_time > last_processed_time:
                        
                        # Double Check: Is this signal from a CLOSED candle?
                        # Signal time (candle start) + 15m should be <= Now
                        # logic: 10:00 candle closes at 10:15. It is safe to alert at 10:15:10.
                        
                        # print(f"Signal Time: {signal_time} | Now: {datetime.now()}")
                        
                        print(f"\n🔥 NEW SIGNAL DETECTED at {signal_time} 🔥")
                        msg = format_signal_message(last_signal)
                        print(msg)
                        
                        # Send Alert
                        send_telegram_message(msg)
                        
                        last_processed_time = signal_time
                    else:
                        print(f"No new signals. (Last: {last_processed_time})")
                else:
                     print(f"No signals found.")
            else:
                print("Error fetching data.")
            
        except KeyboardInterrupt:
            print("\nStopping bot...")
            sys.exit(0)
        except Exception as e:
            print(f"\nError in loop: {e}")
            time.sleep(60) # Failure fallback wait

if __name__ == "__main__":
    run_live_bot()
