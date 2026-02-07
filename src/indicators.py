import pandas as pd
import pandas_ta as ta

def calculate_ema(df, period=20):
    """
    Calculate Exponential Moving Average (EMA).
    
    Args:
        df (pd.DataFrame): DataFrame containing 'close' column.
        period (int): EMA period.
        
    Returns:
        pd.DataFrame: DataFrame with added EMA column.
    """
    if df.empty:
        return df
    
    # Calculate EMA using pandas_ta
    # This adds a column named like 'EMA_20'
    df.ta.ema(length=period, append=True)
    
    return df
