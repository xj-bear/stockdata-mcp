import akshare as ak
import pandas as pd
from datetime import datetime, date, time
from typing import List, Dict, Any, Optional

# Helper to format date
def format_date(date_str: str) -> str:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y%m%d")
    except ValueError:
        return date_str.replace("-", "")

class DataSource:
    @staticmethod
    def search_stock(query: str) -> Optional[str]:
        """
        Search for a stock by name or code. Returns the symbol.
        """
        try:
            # Get real-time quotes which includes all A-shares
            df = ak.stock_zh_a_spot_em()
            # Columns: 序号, 代码, 名称, ...
            # Filter
            mask = df['代码'].astype(str).str.contains(query) | df['名称'].str.contains(query)
            results = df[mask]
            if not results.empty:
                return results.iloc[0]['代码']
            return None

        except Exception as e:
            print(f"Error searching stock (Eastmoney): {e}")
            # Fallback 1: Try stock_info_a_code_name
            try:
                df = ak.stock_info_a_code_name()
                mask = df['code'].astype(str).str.contains(query) | df['name'].str.contains(query)
                results = df[mask]
                if not results.empty:
                    return results.iloc[0]['code']
            except Exception as e2:
                print(f"Error searching stock (Fallback): {e2}")
            
            # Fallback 2: If query is a 6-digit code, return it directly
            if query.isdigit() and len(query) == 6:
                return query
                
            return None

    @staticmethod
    def search_hk_stock(query: str) -> Optional[str]:
        """
        Search for a HK stock by name or code. Returns the symbol.
        """
        try:
            # stock_hk_spot_em
            df = ak.stock_hk_spot_em()
            # Filter
            mask = df['代码'].astype(str).str.contains(query, case=False) | df['名称'].str.contains(query, case=False)
            results = df[mask]
            if not results.empty:
                return results.iloc[0]['代码']
            return None
        except Exception as e:
            print(f"Error searching HK stock (Eastmoney): {e}")
            # Fallback: Try Sina spot
            try:
                df = ak.stock_hk_spot()
                # Columns: 代码, 中文名称, ...
                mask = df['代码'].astype(str).str.contains(query, case=False) | df['中文名称'].str.contains(query, case=False)
                results = df[mask]
                if not results.empty:
                    return results.iloc[0]['代码']
            except Exception as e2:
                print(f"Error searching HK stock (Sina): {e2}")

            if query.isdigit() and len(query) == 5:
                return query
            return None

    @staticmethod
    def search_us_stock(query: str) -> Optional[str]:
        """
        Search for a US stock by name or code. Returns the symbol.
        """
        try:
            # stock_us_spot_em includes all US stocks
            df = ak.stock_us_spot_em()
            # Columns: 序号, 名称, 最新价, ..., 代码
            # Filter
            mask = df['代码'].astype(str).str.contains(query, case=False) | df['名称'].str.contains(query, case=False)
            results = df[mask]
            if not results.empty:
                return results.iloc[0]['代码']
            return None
        except Exception as e:
            print(f"Error searching US stock: {e}")
            # Fallback: if query looks like a symbol (all letters), return it directly
            if query.isalpha():
                return query.upper()
            return None

    @staticmethod
    def _convert_dates(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Helper to convert date/datetime objects to strings in a list of dicts"""
        new_data = []
        for item in data:
            new_item = {}
            for k, v in item.items():
                if isinstance(v, (datetime, pd.Timestamp)):
                    new_item[k] = v.strftime("%Y-%m-%d")
                elif hasattr(v, 'isoformat'): # datetime.date
                    new_item[k] = v.isoformat()
                else:
                    new_item[k] = v
            new_data.append(new_item)
        return new_data



    @staticmethod
    def _add_market_prefix(symbol: str) -> str:
        if symbol.startswith("6") or symbol.startswith("5"):
            return "sh" + symbol
        elif symbol.startswith("0") or symbol.startswith("3") or symbol.startswith("1"):
            return "sz" + symbol
        elif symbol.startswith("4") or symbol.startswith("8"):
            return "bj" + symbol
        return symbol

    @staticmethod
    def _normalize_columns(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize Chinese column names to English"""
        mapping = {
            "日期": "date", "开盘": "open", "收盘": "close", "最高": "high", "最低": "low",
            "成交量": "volume", "成交额": "amount", "振幅": "amplitude", 
            "涨跌幅": "pct_chg", "涨跌额": "chg", "换手率": "turnover",
            "最新价": "close" # For spot data if needed
        }
        new_data = []
        for item in data:
            new_item = {}
            for k, v in item.items():
                new_key = mapping.get(k, k)
                new_item[new_key] = v
            new_data.append(new_item)
        return new_data

    @staticmethod
    def get_stock_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            start = format_date(start_date)
            end = format_date(end_date)
            # Try Eastmoney first
            df = ak.stock_zh_a_hist(symbol=symbol, start_date=start, end_date=end, adjust="qfq")
            return DataSource._convert_dates(DataSource._normalize_columns(df.to_dict(orient="records")))
        except Exception as e:
            print(f"Eastmoney failed: {e}, trying Sina...")
            try:
                # Fallback to Sina
                code = DataSource._add_market_prefix(symbol)
                df = ak.stock_zh_a_daily(symbol=code, start_date=start, end_date=end)
                return DataSource._convert_dates(DataSource._normalize_columns(df.to_dict(orient="records")))
            except Exception as e2:
                return [{"error": f"Failed to fetch stock data (All sources): {str(e)} | {str(e2)}"}]

    @staticmethod
    def get_index_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            # index_zh_a_hist for A-share indices
            df = ak.index_zh_a_hist(symbol=symbol, start_date=format_date(start_date), end_date=format_date(end_date))
            return DataSource._convert_dates(df.to_dict(orient="records"))
        except Exception as e:
            return [{"error": f"Failed to fetch index data: {str(e)}"}]



    @staticmethod
    def get_hk_stock_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        # Handle 4-digit HK codes
        if symbol.isdigit() and len(symbol) == 4:
            symbol = "0" + symbol

        # Try Sina first as it seems more stable for HK
        try:
            # Sina: stock_hk_daily(symbol="00700", adjust="qfq")
            df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
            df['date'] = pd.to_datetime(df['date'])
            s_date = pd.to_datetime(start_date)
            e_date = pd.to_datetime(end_date)
            mask = (df['date'] >= s_date) & (df['date'] <= e_date)
            return DataSource._convert_dates(DataSource._normalize_columns(df[mask].to_dict(orient="records")))
        except Exception as e:
            return [{"error": f"Failed to fetch HK stock data: {str(e)}"}]

    @staticmethod
    def get_fund_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            start = format_date(start_date)
            end = format_date(end_date)
            # Try ETF first (Eastmoney)
            try:
                df = ak.fund_etf_hist_em(symbol=symbol, start_date=start, end_date=end)
                return DataSource._convert_dates(df.to_dict(orient="records"))
            except Exception as e_em:
                print(f"Eastmoney ETF failed: {e_em}, trying Sina...")
                print(f"Eastmoney ETF failed: {e_em}, trying Sina...")
                # Fallback to Sina ETF
                try:
                    # Sina ETF needs prefix (e.g. sh510300)
                    code = DataSource._add_market_prefix(symbol)
                    df = ak.fund_etf_hist_sina(symbol=code)
                    df['date'] = pd.to_datetime(df['date'])
                    s_date = pd.to_datetime(start_date)
                    e_date = pd.to_datetime(end_date)
                    mask = (df['date'] >= s_date) & (df['date'] <= e_date)
                    return DataSource._convert_dates(df[mask].to_dict(orient="records"))
                except:
                    raise e_em # Raise original if both fail

        except Exception as e:
            return [{"error": f"Failed to fetch fund data: {str(e)}"}]

    @staticmethod
    def get_futures_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            # futures_zh_daily_sina
            df = ak.futures_zh_daily_sina(symbol=symbol)
            # Filter by date manually since API might not support start/end
            df['date'] = pd.to_datetime(df['date'])
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            mask = (df['date'] >= start) & (df['date'] <= end)
            return DataSource._convert_dates(df[mask].to_dict(orient="records"))
        except Exception as e:
            return [{"error": f"Failed to fetch futures data: {str(e)}"}]



    @staticmethod
    def get_us_stock_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            start = format_date(start_date)
            end = format_date(end_date)
            # Try Eastmoney first
            df = ak.stock_us_hist(symbol=symbol, start_date=start, end_date=end, adjust="qfq")
            return DataSource._convert_dates(DataSource._normalize_columns(df.to_dict(orient="records")))
        except Exception as e:
            print(f"Eastmoney US failed: {e}, trying Sina...")
            try:
                # Fallback to Sina: stock_us_daily(symbol="AAPL", adjust="qfq")
                # Sina might need lowercase or specific format.
                # Usually Sina uses "AAPL" or "gb_aapl"?
                # ak.stock_us_daily(symbol="AAPL")
                df = ak.stock_us_daily(symbol=symbol, adjust="qfq")
                df['date'] = pd.to_datetime(df['date'])
                s_date = pd.to_datetime(start_date)
                e_date = pd.to_datetime(end_date)
                mask = (df['date'] >= s_date) & (df['date'] <= e_date)
                return DataSource._convert_dates(DataSource._normalize_columns(df[mask].to_dict(orient="records")))
            except Exception as e2:
                return [{"error": f"Failed to fetch US stock data: {str(e)} | {str(e2)}"}]

    @staticmethod
    def get_us_fund_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        # US Funds are often treated as stocks (ETFs)
        return DataSource.get_us_stock_data(symbol, start_date, end_date)

    @staticmethod
    def get_futures_foreign_data(symbol: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            start = format_date(start_date)
            end = format_date(end_date)
            # futures_foreign_hist for foreign futures
            df = ak.futures_foreign_hist(symbol=symbol)
            # Filter by date
            df['date'] = pd.to_datetime(df['date'])
            s_date = pd.to_datetime(start_date)
            e_date = pd.to_datetime(end_date)
            mask = (df['date'] >= s_date) & (df['date'] <= e_date)
            return DataSource._convert_dates(df[mask].to_dict(orient="records"))
        except Exception as e:
            return [{"error": f"Failed to fetch foreign futures data: {str(e)}"}]
    @staticmethod
    def _sanitize_dict(d: Any) -> Any:
        """Recursively convert date/datetime objects to strings and handle NaN"""
        if isinstance(d, dict):
            new_d = {}
            for k, v in d.items():
                new_d[k] = DataSource._sanitize_dict(v)
            return new_d
        elif isinstance(d, list):
            return [DataSource._sanitize_dict(item) for item in d]
        elif isinstance(d, (date, datetime, time)):
            return d.isoformat()
        elif isinstance(d, float) and (pd.isna(d) or d != d): # Check for NaN
            return None
        else:
            return d

    @staticmethod
    def get_stock_info(symbol: str) -> Dict[str, Any]:
        """Get individual stock info"""
        try:
            # Handle 4-digit HK codes
            if symbol.isdigit() and len(symbol) == 4:
                symbol = "0" + symbol

            # Detect market
            is_hk = symbol.isdigit() and len(symbol) == 5
            is_us = not symbol.isdigit()
            
            if is_hk:
                # HK Optimization: Use daily for price + profile for name
                try:
                    # 1. Get Price/Change from daily (latest)
                    # Use qfq to get adjusted price, or just normal? Spot is usually unadjusted.
                    # But daily gives open/close/high/low.
                    # Let's use stock_hk_daily(adjust="") for unadjusted price matching spot.
                    df_daily = ak.stock_hk_daily(symbol=symbol, adjust="")
                    if df_daily.empty:
                         return {"error": f"HK stock {symbol} not found"}
                    
                    latest = df_daily.iloc[-1]
                    # daily columns: date, open, high, low, close, volume, amount, ...
                    # We need change percent. Calculate from previous close?
                    # Or just return what we have.
                    # Let's calculate change if possible.
                    if len(df_daily) > 1:
                        prev = df_daily.iloc[-2]
                        change = latest['close'] - prev['close']
                        change_pct = (change / prev['close']) * 100
                    else:
                        change = 0
                        change_pct = 0
                        
                    info = {
                        "symbol": symbol,
                        "current_price": latest['close'],
                        "change_percent": round(change_pct, 2),
                        "change_amount": round(change, 2),
                        "volume": latest['volume'],
                        "amount": latest.get('amount')
                    }
                    
                    # 2. Get Name from Profile
                    try:
                        df_profile = ak.stock_hk_company_profile_em(symbol=symbol)
                        if not df_profile.empty:
                            profile = df_profile.iloc[0].to_dict()
                            info["name"] = profile.get('公司名称') or profile.get('中文名称')
                            info.update(profile)
                    except:
                        pass
                        
                    return DataSource._sanitize_dict(info)
                except Exception as e:
                    return {"error": f"Failed to fetch HK stock info: {str(e)}"}
            
            elif is_us:
                # US Optimization: Use daily + indicators for name
                try:
                    # 1. Daily for Price
                    df_daily = ak.stock_us_daily(symbol=symbol, adjust="")
                    if df_daily.empty:
                        return {"error": f"US stock {symbol} not found"}
                        
                    latest = df_daily.iloc[-1]
                    if len(df_daily) > 1:
                        prev = df_daily.iloc[-2]
                        change = latest['close'] - prev['close']
                        change_pct = (change / prev['close']) * 100
                    else:
                        change = 0
                        change_pct = 0
                        
                    info = {
                        "symbol": symbol,
                        "current_price": latest['close'],
                        "change_percent": round(change_pct, 2),
                        "change_amount": round(change, 2),
                        "volume": latest['volume']
                    }
                    
                    # 2. Name from Indicators (fast)
                    try:
                        df_ind = ak.stock_financial_us_analysis_indicator_em(symbol=symbol, indicator="年报")
                        if not df_ind.empty:
                            info["name"] = df_ind.iloc[0].get('SECURITY_NAME_ABBR')
                            info["pe"] = df_ind.iloc[0].get('PE') # If available? Usually not in this func but check
                    except:
                        pass
                        
                    return DataSource._sanitize_dict(info)
                except Exception as e:
                    return {"error": f"Failed to fetch US stock info: {str(e)}"}
            
            else:
                # A-share (default) - Keep existing but sanitize
                data = ak.stock_individual_info_em(symbol=symbol)
                res = data.to_dict(orient="records")[0]
                return DataSource._sanitize_dict(res)
        except Exception as e:
            return {"error": f"Failed to fetch stock info: {str(e)}"}

    @staticmethod
    def get_stock_indicators(symbol: str) -> Dict[str, Any]:
        """Get stock financial indicators (Abstract)"""
        try:
            # Handle 4-digit HK codes
            if symbol.isdigit() and len(symbol) == 4:
                symbol = "0" + symbol

            # Detect market
            is_hk = symbol.isdigit() and len(symbol) == 5
            is_us = not symbol.isdigit()
            
            if is_hk:
                # HK: stock_hk_financial_indicator_em
                try:
                    df = ak.stock_hk_financial_indicator_em(symbol=symbol)
                    if not df.empty:
                        latest = df.iloc[0].to_dict()
                        return {
                            "PE": latest.get('市盈率'),
                            "PB": latest.get('市净率'),
                            "DividendYield": latest.get('股息率TTM(%)'),
                            "ROE": latest.get('股东权益回报率(%)'),
                            "NetProfit": latest.get('净利润'),
                            "Revenue": latest.get('营业总收入')
                        }
                    return {"error": "No HK indicators found"}
                except Exception as e:
                    return {"error": f"Failed to fetch HK indicators: {str(e)}"}
            
            elif is_us:
                # US: stock_financial_us_analysis_indicator_em
                try:
                    df = ak.stock_financial_us_analysis_indicator_em(symbol=symbol, indicator="年报")
                    if not df.empty:
                        latest = df.iloc[0].to_dict()
                        return {
                            "EPS": latest.get('BASIC_EPS'),
                            "ROE": latest.get('ROE_AVG'),
                            "ROA": latest.get('ROA'),
                            "GrossMargin": latest.get('GROSS_PROFIT_RATIO'),
                            "NetProfitRatio": latest.get('NET_PROFIT_RATIO'),
                            "Note": "PE/PB not available for US stocks in this source."
                        }
                    return {"error": "No US indicators found"}
                except Exception as e:
                    return {"error": f"Failed to fetch US indicators: {str(e)}"}
            
            else:
                # A-share
                df = ak.stock_financial_abstract(symbol=symbol)
                if not df.empty:
                    latest_date_col = df.columns[2]
                    result = {"date": latest_date_col}
                    for _, row in df.iterrows():
                        indicator_name = row['指标']
                        value = row[latest_date_col]
                        result[indicator_name] = value
                    return result
                return {"error": "No indicator data found"}
        except Exception as e:
            return {"error": f"Failed to fetch indicators: {str(e)}"}

    @staticmethod
    def get_financial_report(symbol: str) -> Dict[str, Any]:
        """Get detailed financial report abstract"""
        try:
            # Handle 4-digit HK codes
            if symbol.isdigit() and len(symbol) == 4:
                symbol = "0" + symbol

            # Detect market
            is_hk = symbol.isdigit() and len(symbol) == 5
            is_us = not symbol.isdigit()
            
            if is_hk:
                # HK: stock_financial_hk_analysis_indicator_em
                try:
                    # Use "报告期" to get quarterly data
                    df = ak.stock_financial_hk_analysis_indicator_em(symbol=symbol, indicator="报告期")
                    if not df.empty:
                        # Sort by REPORT_DATE descending and take top 8 (2 years)
                        df['REPORT_DATE'] = pd.to_datetime(df['REPORT_DATE'])
                        df = df.sort_values('REPORT_DATE', ascending=False).head(8)
                        
                        dates = df['REPORT_DATE'].dt.strftime('%Y-%m-%d').tolist()
                        
                        # Map metrics
                        metrics = {
                            "Revenue": df['OPERATE_INCOME'].tolist(),
                            "NetProfit": df['HOLDER_PROFIT'].tolist(),
                            "EPS": df['BASIC_EPS'].tolist(),
                            "ROE": df['ROE_AVG'].tolist(),
                            "ROA": df['ROA'].tolist(),
                            "GrossMargin": df['GROSS_PROFIT_RATIO'].tolist(),
                            "NetProfitMargin": df['NET_PROFIT_RATIO'].tolist()
                        }
                        
                        return {
                            "symbol": symbol,
                            "dates": dates,
                            "metrics": metrics
                        }
                    return {"error": "No HK financial data found"}
                except Exception as e:
                    return {"error": f"Failed to fetch HK financial report: {str(e)}"}
            
            elif is_us:
                # US: stock_financial_us_analysis_indicator_em
                try:
                    # US only supports "年报" (Annual)
                    df = ak.stock_financial_us_analysis_indicator_em(symbol=symbol, indicator="年报")
                    if not df.empty:
                        # Sort by REPORT_DATE descending and take top 8
                        df['REPORT_DATE'] = pd.to_datetime(df['REPORT_DATE'])
                        df = df.sort_values('REPORT_DATE', ascending=False).head(8)
                        
                        dates = df['REPORT_DATE'].dt.strftime('%Y-%m-%d').tolist()
                        
                        # Map metrics
                        metrics = {
                            "Revenue": df['OPERATE_INCOME'].tolist(),
                            "NetProfit": df['PARENT_HOLDER_NETPROFIT'].tolist(),
                            "EPS": df['BASIC_EPS'].tolist(),
                            "ROE": df['ROE_AVG'].tolist(),
                            "ROA": df['ROA'].tolist(),
                            "GrossMargin": df['GROSS_PROFIT_RATIO'].tolist(),
                            "NetProfitMargin": df['NET_PROFIT_RATIO'].tolist()
                        }
                        
                        return {
                            "symbol": symbol,
                            "dates": dates,
                            "metrics": metrics
                        }
                    return {"error": "No US financial data found"}
                except Exception as e:
                    return {"error": f"Failed to fetch US financial report: {str(e)}"}

            else:
                # A-share financial abstract
                df = ak.stock_financial_abstract(symbol=symbol)
                if not df.empty:
                    date_columns = df.columns[2:7]
                    result = {
                        "symbol": symbol,
                        "dates": list(date_columns),
                        "metrics": {}
                    }
                    for _, row in df.iterrows():
                        indicator_name = row['指标']
                        values = []
                        for col in date_columns:
                            val = row[col]
                            try:
                                val = float(val)
                            except:
                                pass
                            values.append(val)
                        result["metrics"][indicator_name] = values
                    return result
                return {"error": "No financial data found"}
        except Exception as e:
            return {"error": f"Failed to fetch financial report: {str(e)}"}

    @staticmethod
    def get_trading_suggest(symbol: str) -> Dict[str, Any]:
        """Calculate simple trading suggestions based on technical indicators"""
        try:
            # Handle 4-digit HK codes
            if symbol.isdigit() and len(symbol) == 4:
                symbol = "0" + symbol

            # Get last 60 days of data for calculation
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - pd.Timedelta(days=100)).strftime("%Y%m%d")
            
            # Detect market and fetch data
            is_hk = symbol.isdigit() and len(symbol) == 5
            is_us = not symbol.isdigit()
            
            if is_hk:
                data_list = DataSource.get_hk_stock_data(symbol, start_date, end_date)
            elif is_us:
                data_list = DataSource.get_us_stock_data(symbol, start_date, end_date)
            else:
                data_list = DataSource.get_stock_data(symbol, start_date, end_date)
                
            if not data_list or (isinstance(data_list, list) and len(data_list) > 0 and "error" in data_list[0]):
                return {"error": "Insufficient data for analysis"}
            
            df = pd.DataFrame(data_list)
            if df.empty:
                 return {"error": "Insufficient data for analysis"}
                 
            df['close'] = pd.to_numeric(df['close'])
            
            # Calculate Indicators
            # MA
            df['MA5'] = df['close'].rolling(window=5).mean()
            df['MA20'] = df['close'].rolling(window=20).mean()
            
            # RSI (Simple 14-day)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            
            suggestions = []
            
            # MA Cross
            if latest['MA5'] > latest['MA20'] and prev['MA5'] <= prev['MA20']:
                suggestions.append("MA Golden Cross (Bullish): MA5 crossed above MA20.")
            elif latest['MA5'] < latest['MA20'] and prev['MA5'] >= prev['MA20']:
                suggestions.append("MA Death Cross (Bearish): MA5 crossed below MA20.")
            
            # Trend
            if latest['MA5'] > latest['MA20']:
                trend = "Bullish"
            else:
                trend = "Bearish"
                
            # RSI
            rsi_val = latest['RSI']
            if rsi_val > 70:
                suggestions.append(f"RSI Overbought ({rsi_val:.2f}): Consider selling.")
            elif rsi_val < 30:
                suggestions.append(f"RSI Oversold ({rsi_val:.2f}): Consider buying.")
            
            return {
                "symbol": symbol,
                "date": latest['date'],
                "price": latest['close'],
                "MA5": round(latest['MA5'], 2),
                "MA20": round(latest['MA20'], 2),
                "RSI": round(rsi_val, 2),
                "trend": trend,
                "suggestions": suggestions if suggestions else ["Hold / No clear signal"]
            }
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    @staticmethod
    def get_stock_zt_pool(date: str) -> List[Dict[str, Any]]:
        """Get limit-up stock pool for a specific date (YYYYMMDD)"""
        try:
            # akshare expects YYYYMMDD
            date_str = date.replace("-", "")
            df = ak.stock_zt_pool_em(date=date_str)
            return df.to_dict(orient="records")
        except Exception as e:
            return [{"error": f"Failed to fetch limit-up pool: {str(e)}"}]

    @staticmethod
    def get_stock_lhb(date: str) -> List[Dict[str, Any]]:
        """Get Dragon-Tiger list statistics for a specific date"""
        try:
            date_str = date.replace("-", "")
            df = ak.stock_lhb_ggtj_sina(date=date_str)
            return df.to_dict(orient="records")
        except Exception as e:
            return [{"error": f"Failed to fetch LHB data: {str(e)}"}]

    @staticmethod
    def get_sector_fund_flow() -> List[Dict[str, Any]]:
        """Get sector fund flow ranking (Today)"""
        try:
            df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            return df.to_dict(orient="records")
        except Exception as e:
            return [{"error": f"Failed to fetch sector fund flow: {str(e)}"}]

    @staticmethod
    def get_stock_news(symbol: str) -> List[Dict[str, Any]]:
        """Get news for a specific stock"""
        try:
            # Handle 4-digit HK codes
            if symbol.isdigit() and len(symbol) == 4:
                symbol = "0" + symbol

            df = ak.stock_news_em(symbol=symbol)
            # Limit to top 10
            return df.head(10).to_dict(orient="records")
        except Exception as e:
            return [{"error": f"Failed to fetch stock news: {str(e)}"}]

    @staticmethod
    def get_global_news() -> List[Dict[str, Any]]:
        """Get global financial news"""
        try:
            # Cailian Press Global News
            df = ak.stock_info_global_cls()
            records = df.head(20).to_dict(orient="records")
            return DataSource._sanitize_dict(records)
        except Exception as e:
            return [{"error": f"Failed to fetch global news: {str(e)}"}]

