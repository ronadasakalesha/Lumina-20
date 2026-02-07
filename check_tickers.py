import requests
from src.config import BASE_URL

def get_btc_tickers():
    url = f"{BASE_URL}/v2/tickers"
    try:
        response = requests.get(url)
        data = response.json()
        
        if "result" in data:
            tickers = data["result"]
            
            print(f"{'Symbol':<30} | {'Mark Price':<15} | {'Close Price':<15}")
            print("-" * 65)
            
            for t in tickers:
                symbol = t["symbol"]
                mark_price = t.get("mark_price")
                close_price = t.get("close")
                
                mark_price_val = 0
                close_price_val = 0
                
                try:
                    mark_price_val = float(mark_price) if mark_price is not None else 0
                    mark_price_str = f"{mark_price_val:.2f}"
                except (ValueError, TypeError):
                     mark_price_str = str(mark_price)
                     
                try:
                    close_price_val = float(close_price) if close_price is not None else 0
                    close_price_str = f"{close_price_val:.2f}"
                except (ValueError, TypeError):
                    close_price_str = str(close_price)

                # Filter for prices > 70000
                if mark_price_val > 70000 or close_price_val > 70000:
                    print(f"{symbol:<30} | {mark_price_str:<15} | {close_price_str:<15}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_btc_tickers()
