import json
from data_source import DataSource
from datetime import datetime, timedelta

def run_test(name, func, *args):
    print(f"\n--- Testing {name} ---")
    try:
        result = func(*args)
        print(f"Result type: {type(result)}")
        if isinstance(result, list) and len(result) > 0:
            print(f"First item: {result[0]}")
            if "error" in result[0]:
                print(f"Status: FAILED (Error returned: {result[0]['error']})")
            else:
                print("Status: SUCCESS")
        else:
            print(f"Result: {result}")
            if result:
                 print("Status: SUCCESS")
            else:
                 print("Status: EMPTY/NONE")
    except Exception as e:
        print(f"Status: CRASHED ({e})")

def main():
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f"Test Date Range: {start_date} to {end_date}")

    # 1. A-Share Stock
    print("\n[1] A-Share Stock")
    symbol = DataSource.search_stock("茅台")
    print(f"Search '茅台': {symbol}")
    if symbol:
        run_test("get_stock_data (Moutai)", DataSource.get_stock_data, symbol, start_date, end_date)
    
    symbol = DataSource.search_stock("600519")
    print(f"Search '600519': {symbol}")

    # 2. US Stock
    print("\n[2] US Stock")
    symbol = DataSource.search_us_stock("Apple")
    print(f"Search 'Apple': {symbol}")
    if symbol:
        run_test("get_us_stock_data (Apple)", DataSource.get_us_stock_data, symbol, start_date, end_date)
    
    symbol = DataSource.search_us_stock("AAPL") # Should work via fallback or search
    print(f"Search 'AAPL': {symbol}")
    if symbol:
        run_test("get_us_stock_data (AAPL)", DataSource.get_us_stock_data, symbol, start_date, end_date)

    # 3. US Fund (ETF)
    print("\n[3] US Fund (ETF)")
    # SPY is a common ETF
    symbol = "105.SPY" # akshare might need specific format for US stocks/ETFs if using stock_us_hist? 
    # Actually stock_us_hist usually takes "105.SPY" or similar for eastmoney, or just "SPY" if the search returns it correctly.
    # Let's rely on search_us_stock to find the code format akshare needs.
    symbol = DataSource.search_us_stock("SPY")
    print(f"Search 'SPY': {symbol}")
    if symbol:
        run_test("get_us_fund_data (SPY)", DataSource.get_us_fund_data, symbol, start_date, end_date)

    # 4. Foreign Futures
    print("\n[4] Foreign Futures")
    # A50 usually has a specific code. Let's try "CN" (SGX A50) or similar if we knew it.
    # For now, let's try a known symbol if possible, or just test the function with a likely symbol.
    # 'CON' is Crude Oil often? Or 'CL'? 
    # akshare futures_foreign_hist might use specific codes.
    # Let's try 'ZNC' (Zinc) or 'LRC' (Lead) or 'OIL' if supported.
    # Actually, let's try 'DAX' or 'NAS' if they are indices/futures.
    # Let's try a generic one if we can't search.
    run_test("get_futures_foreign_data (Test Symbol 'CL')", DataSource.get_futures_foreign_data, "CL", start_date, end_date)

    # 5. Singapore Options
    # 5. Singapore Options - Removed as method not present
    # run_test("get_sg_options_data", DataSource.get_sg_options_data, "Any", start_date, end_date)
    pass

if __name__ == "__main__":
    main()
