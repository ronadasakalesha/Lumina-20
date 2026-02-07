import pandas as pd

def apply_strategy(df):
    """
    Apply 20 EMA strategy rules to the DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame with 'close' and 'EMA_20' columns.
        
    Returns:
        pd.DataFrame: DataFrame with 'signal' column (1 for Buy, -1 for Sell, 0 for Hold).
    """
    if 'EMA_20' not in df.columns:
        print("EMA_20 column missing.")
        return df
    
    df['signal'] = 0
    
    df['signal'] = 0
    df['reason'] = '' # To store the reason for the signal
    
    # Identify candle color and EMA relation
    df['is_green'] = df['close'] > df['open']
    df['is_red'] = df['close'] < df['open']
    df['above_ema'] = df['close'] > df['EMA_20']
    df['below_ema'] = df['close'] < df['EMA_20']
    
    df['below_ema'] = df['close'] < df['EMA_20']
    
    df['entry_signal'] = 0
    df['entry_price'] = 0.0
    df['stop_loss'] = 0.0
    df['take_profit'] = 0.0
    df['exit_signal'] = 0
    df['exit_price'] = 0.0
    
    # Iterate to find patterns
    # We need to look ahead, so we iterate up to len(df) - 2
    for i in range(len(df) - 2):
        # ---------------------------------------------------------
        # BUY SCENARIO
        # ---------------------------------------------------------
        # Step 1: Breakout (Green candle CROSSING and closing above EMA)
        # Condition: Green Candle + Close > EMA + Open < EMA
        if df.iloc[i]['is_green'] and df.iloc[i]['above_ema'] and (df.iloc[i]['open'] < df.iloc[i]['EMA_20']):
            # Step 2: Confirmation (Next 2 candles)
            c1_idx = i + 1
            c2_idx = i + 2
            
            c1 = df.iloc[c1_idx]
            c2 = df.iloc[c2_idx]
            
            setup_candle_idx = -1
            trigger_price = 0.0
            sl_price = 0.0
            
            # Case A: Next candle (i+1) is Red and Closes Above EMA
            if c1['is_red'] and c1['above_ema']:
                 setup_candle_idx = c1_idx
                 trigger_price = c1['high']
                 sl_price = c1['low'] # SL at Low of setup candle
                 df.at[c1_idx, 'signal'] = 1 
                 df.at[c1_idx, 'reason'] = 'Buy Setup Confirmed'
                 df.at[c1_idx, 'trigger_price'] = trigger_price
                 df.at[c1_idx, 'stop_loss'] = sl_price
                 
            # Case B: Candle (i+1) is Green, Candle (i+2) is Red and Closes Above EMA
            elif c2['is_red'] and c2['above_ema']:
                 setup_candle_idx = c2_idx
                 trigger_price = c2['high']
                 sl_price = c2['low'] # SL at Low of setup candle
                 df.at[c2_idx, 'signal'] = 1 
                 df.at[c2_idx, 'reason'] = 'Buy Setup Confirmed'
                 df.at[c2_idx, 'trigger_price'] = trigger_price
                 df.at[c2_idx, 'stop_loss'] = sl_price

            # Step 3, 5 & 6: Entry Trigger, SL Check, and TP Check
            if setup_candle_idx != -1:
                in_trade = False
                current_tp = 0.0
                current_sl = 0.0
                
                # Look forward for entry and trade management
                for k in range(setup_candle_idx + 1, min(setup_candle_idx + 50, len(df))): # Extended lookahead for trade duration
                    # If not in trade, look for entry
                    if not in_trade:
                        if df.iloc[k]['high'] > trigger_price:
                            df.at[k, 'entry_signal'] = 1
                            df.at[k, 'entry_price'] = trigger_price
                            
                            # Calculate Risk and Target
                            risk = trigger_price - sl_price
                            target = trigger_price + (4 * risk)
                            
                            current_sl = sl_price
                            current_tp = target
                            
                            df.at[k, 'stop_loss'] = current_sl
                            df.at[k, 'take_profit'] = current_tp
                            df.at[k, 'reason'] = f"Buy Triggered. Target: {target:.2f}"
                            in_trade = True
                    
                    # If in trade, look for Exit (SL or TP)
                    else: 
                        df.at[k, 'stop_loss'] = current_sl
                        df.at[k, 'take_profit'] = current_tp
                        
                        # Check TP (High captures Target)
                        if df.iloc[k]['high'] >= current_tp:
                            df.at[k, 'exit_signal'] = 2 # 2 for Target Hit
                            df.at[k, 'exit_price'] = current_tp
                            df.at[k, 'reason'] = f"Target Hit ({current_tp:.2f})"
                            break # Trade finished
                        
                        # Check SL (Close crosses SL)
                        if df.iloc[k]['close'] < current_sl:
                            df.at[k, 'exit_signal'] = 1 # 1 for SL Hit
                            df.at[k, 'exit_price'] = df.iloc[k]['close'] # Aproximation
                            df.at[k, 'reason'] = f"SL Hit (Close {df.iloc[k]['close']} < {current_sl})"
                            break # Trade finished

        # ---------------------------------------------------------
        # SELL SCENARIO
        # ---------------------------------------------------------
        # Step 1: Breakdown (Red candle CROSSING and closing below EMA)
        # Condition: Red Candle + Close < EMA + Open > EMA
        if df.iloc[i]['is_red'] and df.iloc[i]['below_ema'] and (df.iloc[i]['open'] > df.iloc[i]['EMA_20']):
            # Step 2: Confirmation
            c1_idx = i + 1
            c2_idx = i + 2
            
            c1 = df.iloc[c1_idx]
            c2 = df.iloc[c2_idx]
            
            setup_candle_idx = -1
            trigger_price = 0.0
            sl_price = 0.0
            
            # Case A: Next candle (i+1) is Green and Closes Below EMA
            if c1['is_green'] and c1['below_ema']:
                 setup_candle_idx = c1_idx
                 trigger_price = c1['low']
                 sl_price = c1['high'] # SL at High of setup candle
                 df.at[c1_idx, 'signal'] = -1 
                 df.at[c1_idx, 'reason'] = 'Sell Setup Confirmed'
                 df.at[c1_idx, 'trigger_price'] = trigger_price
                 df.at[c1_idx, 'stop_loss'] = sl_price
                 
            # Case B: Candle (i+1) is Red, Candle (i+2) is Green and Closes Below EMA
            elif c2['is_green'] and c2['below_ema']:
                 setup_candle_idx = c2_idx
                 trigger_price = c2['low']
                 sl_price = c2['high'] # SL at High of setup candle
                 df.at[c2_idx, 'signal'] = -1 
                 df.at[c2_idx, 'reason'] = 'Sell Setup Confirmed'
                 df.at[c2_idx, 'trigger_price'] = trigger_price
                 df.at[c2_idx, 'stop_loss'] = sl_price

            # Step 3, 5 & 6: Entry Trigger, SL Check, and TP Check
            if setup_candle_idx != -1:
                in_trade = False
                current_tp = 0.0
                current_sl = 0.0
                
                for k in range(setup_candle_idx + 1, min(setup_candle_idx + 50, len(df))):
                    if not in_trade:
                        if df.iloc[k]['low'] < trigger_price:
                            df.at[k, 'entry_signal'] = -1
                            df.at[k, 'entry_price'] = trigger_price
                            
                            # Calculate Risk and Target
                            risk = sl_price - trigger_price
                            target = trigger_price - (4 * risk)
                            
                            current_sl = sl_price
                            current_tp = target
                            
                            df.at[k, 'stop_loss'] = current_sl
                            df.at[k, 'take_profit'] = current_tp
                            df.at[k, 'reason'] = f"Sell Triggered. Target: {target:.2f}"
                            in_trade = True
                    else:
                        df.at[k, 'stop_loss'] = current_sl
                        df.at[k, 'take_profit'] = current_tp
                        
                        # Check TP (Low captures Target)
                        if df.iloc[k]['low'] <= current_tp:
                            df.at[k, 'exit_signal'] = 2 # 2 for Target Hit
                            df.at[k, 'exit_price'] = current_tp
                            df.at[k, 'reason'] = f"Target Hit ({current_tp:.2f})"
                            break 
                            
                        # Check SL (Close crosses SL)
                        if df.iloc[k]['close'] > current_sl:
                            df.at[k, 'exit_signal'] = 1 
                            df.at[k, 'exit_price'] = df.iloc[k]['close']
                            df.at[k, 'reason'] = f"SL Hit (Close {df.iloc[k]['close']} > {current_sl})"
                            break 
    return df
