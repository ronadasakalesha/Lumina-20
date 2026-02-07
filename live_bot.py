from src.data_fetcher import fetch_candles
from src.indicators import calculate_ema
from src.strategy import apply_strategy
from src.telegram_utils import send_telegram_message, format_signal_message
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
from src.config import TICKERS

def get_seconds_to_next_candle(interval_minutes=15):
    """
    Calculate seconds to sleep until the next candle close.
    """
    now = datetime.now()
    next_minute = (now.minute // interval_minutes + 1) * interval_minutes
    next_run_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=next_minute)
    seconds_to_wait = (next_run_time - now).total_seconds()
    return max(0, seconds_to_wait)

def run_live_bot():
    print(f"✨ Starting Lumina 20 Strategy Bot for {TICKERS} (High-Frequency Monitor)...")
    print("Press Ctrl+C to stop.")
    
    # Watchlist: Stores symbols waiting for entry trigger
    # Structure: { 'SYMBOL': { 'trigger': price, 'type': 'BUY/SELL', 'sl': price, 'tp': price, 'setup_time': timestamp } }
    watchlist = {}
    
    # State tracking for 15m analysis
    last_analysis_time = 0
    buffer_seconds = 10 
    
    while True:
        try:
            now_ts = time.time()
            now_dt = datetime.now()
            
            # ------------------------------------------------------------------
            # PART 1: 15-Minute Analysis (Structure Update)
            # ------------------------------------------------------------------
            # Calculate next expected candle close time
            # We run analysis 10s AFTER the candle closes.
            # E.g., if now is 10:15:10, we run analysis for the 10:00-10:15 candle.
            
            # Next candle close logic check
            # We want to run this exactly once per interval.
            # Simple approach: Check if (now_minutes % 15 == 0) and seconds < 60? 
            # Better: Track last_analysis_time.
            
            # Align to 15m grid
            current_interval_start = now_dt.replace(minute=(now_dt.minute // 15) * 15, second=0, microsecond=0)
            
            # If we haven't analyzed this interval yet, and it's past the buffer time
            # (e.g., 10:15:10), then run analysis.
            time_since_boundary = (now_dt - current_interval_start).total_seconds()
            
            should_analyze = False
            if time_since_boundary >= buffer_seconds and time_since_boundary < buffer_seconds + 60:
                # We are in the "Analysis Window"
                if last_analysis_time != current_interval_start.timestamp():
                    should_analyze = True
                    last_analysis_time = current_interval_start.timestamp()
            
            if should_analyze:
                print(f"\n[{now_dt.strftime('%H:%M:%S')}] 🧠 Running 15m Structure Analysis...")
                
                # Fetch & Analyze History
                end_time = int(now_dt.timestamp())
                start_time = int((now_dt - timedelta(days=2)).timestamp())
                
                for symbol in TICKERS:
                    try:
                        # Clear existing watchlist for this symbol (refreshing state)
                        if symbol in watchlist:
                            del watchlist[symbol]
                            
                        df = fetch_candles(symbol, "15m", start=start_time, end=end_time)
                        
                        if not df.empty:
                            df = calculate_ema(df, period=20)
                            df = apply_strategy(df)
                            
                            # Find the latest "Setup" (Signal = 1/-1) that hasn't been triggered/invalidated
                            # Logic: iterate backwards or check signal columns?
                            # apply_strategy marks 'signal' (Setup) and 'entry_signal' (Trigger).
                            # We want to find a setup where entry_signal hasn't happened yet.
                            
                            # Let's verify the last few candles for a setup
                            recent_df = df.tail(10)
                            
                            # Filter for setups (signal != 0)
                            setups = recent_df[recent_df['signal'] != 0]
                            if not setups.empty:
                                last_setup = setups.iloc[-1]
                                setup_idx = last_setup.name
                                setup_type = "BUY" if last_setup['signal'] == 1 else "SELL"
                                
                                # Check if this setup is still pending
                                # It's pending if price hasn't crossed trigger OR stop loss since setup
                                # AND we are not "in trade" (entry_signal generated).
                                
                                # Check candles AFTER the setup
                                # (Note: apply_strategy lookahead might have already marked entry_signal if it happened in history)
                                # But we want to catch it LIVE if it's happening right NOW or in future.
                                
                                # If the DataFrame row for "now" (or future) isn't there, apply_strategy can't see it.
                                # So we look at the result.
                                
                                # Has an entry triggered AFTER this setup?
                                entries = recent_df.loc[setup_idx+1:][recent_df['entry_signal'] != 0]
                                
                                if entries.empty:
                                    # No entry triggered historically. 
                                    # Is it invalidated? (SL hit?)
                                    # Check high/low of candles after setup
                                    sl_hit = False
                                    trigger_price = last_setup['trigger_price']
                                    sl_price = last_setup['stop_loss']
                                    
                                    # Verify validity
                                    # For Buy: Low should not go below SL
                                    # For Sell: High should not go above SL
                                    candles_after = recent_df.loc[setup_idx+1:]
                                    
                                    for idx, row in candles_after.iterrows():
                                        if setup_type == "BUY" and row['low'] <= sl_price: sl_hit = True
                                        if setup_type == "SELL" and row['high'] >= sl_price: sl_hit = True
                                    
                                    if not sl_hit:
                                        # SETUP IS VALID AND PENDING!
                                        watchlist[symbol] = {
                                            'trigger': trigger_price,
                                            'sl': sl_price,
                                            'type': setup_type,
                                            'time': last_setup['time']
                                        }
                                        print(f"   👀 Watching {symbol} for {setup_type} at {trigger_price}")
                                    else:
                                        print(f"   x {symbol} Setup Invalidated (SL Hit).")
                                else:
                                    # Entry already happened in history
                                    # We could alert this if it was very recent (like in the last closed candle)
                                    # But for High-Freq monitor, we care about future.
                                    # The "Stale Alert" logic handles closed candle alerts.
                                    # We can assume the 15m polling handled the "Just Closed" alert.
                                    pass
                            else:
                                pass # No recent setups
                    except Exception as e:
                        print(f"   x Error analyzing {symbol}: {e}")
                
                print(f"   📋 Active Watchlist: {list(watchlist.keys())}")


            # ------------------------------------------------------------------
            # PART 2: High-Frequency Monitoring (1s Polling)
            # ------------------------------------------------------------------
            if watchlist:
                for symbol in list(watchlist.keys()): # List to allow modification
                    try:
                        data = watchlist[symbol]
                        current_price = get_current_price(symbol)
                        
                        if current_price:
                            triggered = False
                            
                            # Check Trigger Condition
                            if data['type'] == "BUY":
                                if current_price > data['trigger']:
                                    triggered = True
                            elif data['type'] == "SELL":
                                if current_price < data['trigger']:
                                    triggered = True
                                    
                            if triggered:
                                print(f"\n🚀 {symbol} TRIGGERED! Price: {current_price} (Trigger: {data['trigger']})")
                                
                                # Calculate TP/SL for message
                                risk = data['trigger'] - data['sl'] if data['type'] == "BUY" else data['sl'] - data['trigger']
                                target = data['trigger'] + (4*risk) if data['type'] == "BUY" else data['trigger'] - (4*risk)
                                
                                msg = (
                                    f"⚡ INSTANT ALERT: {symbol}\n"
                                    f"Type: {data['type']}\n"
                                    f"Entry: {data['trigger']}\n"
                                    f"Current: {current_price}\n"
                                    f"SL: {data['sl']}\n"
                                    f"TP: {target:.2f} (1:4)"
                                )
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
