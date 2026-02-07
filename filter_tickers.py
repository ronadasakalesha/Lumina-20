try:
    with open("tickers_output.txt", "r", encoding="utf-16") as f:
        lines = f.readlines()
except UnicodeError:
    with open("tickers_output.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
except Exception:
    with open("tickers_output.txt", "r") as f: # default
        lines = f.readlines()

print(f"{'Symbol':<30} | {'Mark Price':<15} | {'Close Price':<15}")
print("-" * 65)

for line in lines:
    parts = line.split("|")
    if len(parts) >= 3:
        try:
            symbol = parts[0].strip()
            mark_price = float(parts[1].strip())
            close_price = float(parts[2].strip())
            
            # Check if either price is close to 70739 (e.g., within 100 points)
            if abs(mark_price - 70739) < 200 or abs(close_price - 70739) < 200:
                print(line.strip())
        except ValueError:
            continue
