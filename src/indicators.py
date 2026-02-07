import pandas as pd


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
    
    # Calculate EMA using native pandas
    # span=period corresponds to the standard EMA calculation
    df[f'EMA_{period}'] = df['close'].ewm(span=period, adjust=False).mean()
    
    return df
