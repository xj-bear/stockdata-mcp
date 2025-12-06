from data_source import DataSource
from datetime import datetime, timedelta
import json

def run_test(name, func, *args):
    print(f"\n--- Testing {name} ---")
    try:
        result = func(*args)
        if isinstance(result, list) and len(result) > 0:
            if "error" in result[0]:
                print(f"Status: FAILED (Error: {result[0]['error']})")
            else:
                print(f"Status: SUCCESS (Records: {len(result)})")
                print(f"Sample: {result[0]}")
        else:
            print(f"Status: EMPTY/NONE (Result: {result})")
    except Exception as e:
        print(f"Status: CRASHED ({e})")

def main():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    
    print(f"Test Date Range: {start_date} to {end_date}")

    # 1. A-Share (Moutai)
    print("\n[1] A-Share (Moutai)")
    symbol = DataSource.search_stock("茅台")
    if not symbol: symbol = "600519"
    run_test("get_stock_data", DataSource.get_stock_data, symbol, start_date, end_date)

    # 2. HK Stock (Tencent)
    print("\n[2] HK Stock (Tencent)")
    # Try search first
    symbol = DataSource.search_hk_stock("腾讯")
    if not symbol: symbol = "00700"
    print(f"Symbol: {symbol}")
    run_test("get_hk_stock_data", DataSource.get_hk_stock_data, symbol, start_date, end_date)

    # 3. US Stock (Apple)
    print("\n[3] US Stock (Apple)")
    symbol = DataSource.search_us_stock("Apple")
    if not symbol: symbol = "AAPL" # Fallback manual
    # Sina US stock symbol format might be different, let's see if fallback handles it.
    # Usually Sina uses lowercase 'aapl' or 'gb_aapl'? 
    # ak.stock_us_daily(symbol="AAPL") usually works.
    print(f"Symbol: {symbol}")
    run_test("get_us_stock_data", DataSource.get_us_stock_data, symbol, start_date, end_date)

    # 4. Fund (ETF - HS300)
    print("\n[4] Fund (HS300 ETF)")
    symbol = "510300"
    run_test("get_fund_data", DataSource.get_fund_data, symbol, start_date, end_date)

    # 5. Futures (Rebar)
    print("\n[5] Futures (Rebar - rb2405 or similar)")
    # Futures symbols change. Let's try a generic continuous one if possible, or a specific active one.
    # 'V2405' (PVC)? 'RB2405'? 
    # akshare futures_zh_daily_sina uses specific contract names like "RB0" (continuous)?
    # Let's try "RB0" for continuous Rebar.
    symbol = "RB0" 
    run_test("get_futures_data", DataSource.get_futures_data, symbol, start_date, end_date)

if __name__ == "__main__":
    main()
