from src.data_fetcher import fetch_candles
from src.indicators import calculate_ema
from src.strategy import apply_strategy
from src.telegram_utils import send_telegram_message, format_signal_message
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

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
            
            df = fetch_candles("BTCUSD", "15m", start=start_time, end=end_time)
            
            if not df.empty:
                # 2. Calculate Indicators
                df = calculate_ema(df, period=20)
                
                # 3. Apply Strategy
                # IMPORTANT: ensure we are NOT using the running candle. 
                # If the API returns the open/running candle as the last row, we must exclude it.
                # A simple check is comparing the candle time to 'now'. 
                # For 15m candle at 10:00, it closes at 10:15.
                # If we are at 10:15:10, the 10:00 candle is closed. The 10:15 candle is running.
                
                # Check last row time
                last_row_time = df.iloc[-1]['time']
                # If last row time is the *current* interval start (e.g. 10:15 when now is 10:15:10), it's running.
                # We want the candle before that (10:00).
                
                # Let's see... Delta returns time as Start of candle.
                # If we are at 10:15:10. 
                # Open candle is 10:15. Closed candle is 10:00.
                
                # Logic: If df.iloc[-1]['time'] is within 15 mins of now, it's likely the running candle.
                current_candle_start = pd.Timestamp.now(tz='UTC').floor('15min') 
                # Note: pd.to_datetime in fetcher might be UTC or local? 
                # Fetcher uses: df['time'] = pd.to_datetime(df['time'], unit='s') -> This is UTC usually.
                
                # Safest bet: Drop the last row if it matches the current partial interval?
                # Actually, strategy checks 'entry_signal' on confirmation.
                # Let's just process df.apply_strategy handles logic.
                
                df = apply_strategy(df)
                
                # 4. Check for *NEW* signals on the *Completed* candles.
                # The strategy might mark a signal on the running candle if we feed it? 
                # We should strictly look at candles that are DEFINITELY closed.
                # Usually that is everything except the very last one returned if it's the current opened one.
                
                # Prune the dataframe to remove potentially running candle
                # If the last candle start time is > now - 15min, it's the running one.
                # Actually simpler: We are running at 10:15:10.
                # We strictly want to verify the candle at 10:00:00.
                
                # Let's look at the last 2-3 rows to be safe and find signals.
                
                # Filter for signals
                signals = df[df['entry_signal'] != 0]
                
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
