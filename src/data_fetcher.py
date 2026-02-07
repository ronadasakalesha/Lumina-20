import requests
import pandas as pd
from datetime import datetime
from src.config import BASE_URL

def fetch_candles(symbol, interval, start=None, end=None):
    """
    Fetch historical candle data from Delta Exchange India.
    
    Args:
        symbol (str): Trading pair symbol (e.g., "BTCUSD").
        interval (str): Time interval (e.g., "1m", "5m", "1h", "1d").
        start (int, optional): Start timestamp in seconds.
        end (int, optional): End timestamp in seconds.
    
    Returns:
        pd.DataFrame: DataFrame containing candle data.
    """
    url = f"{BASE_URL}/v2/history/candles"
    params = {
        "symbol": symbol,
        "resolution": interval
    }
    if start:
        params["start"] = start
    if end:
        params["end"] = end
        
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data and data["result"]:
            df = pd.DataFrame(data["result"], columns=["time", "open", "high", "low", "close", "volume"])
            df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
            df = df.sort_values("time").reset_index(drop=True)
            
            # Convert numeric columns to float
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = df[col].astype(float)
            return df
        else:
            print(f"No data returned for {symbol}")
            return pd.DataFrame()
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching candles: {e}")
        return pd.DataFrame()

def get_ticker_info(symbol):
    """
    Get current ticker information for a symbol.
    """
    url = f"{BASE_URL}/v2/tickers"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if "result" in data:
            for ticker in data["result"]:
                if ticker["symbol"] == symbol:
                    return ticker
        return None
    except requests.exceptions.RequestException as e:
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ticker: {e}")
        return None

def get_current_price(symbol):
    """
    Get the latest mark price/close price for a symbol efficiently.
    Using standard /v2/tickers endpoint as it is the standard public endpoint.
    """
    ticker = get_ticker_info(symbol)
    if ticker and 'close' in ticker:
        return float(ticker['close'])
    return None
