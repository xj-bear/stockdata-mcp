import os
import sys
import asyncio
import json
from datetime import datetime
import akshare as ak
import pandas as pd
from typing import Any, List, Dict
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import Response
import uvicorn
from data_source import DataSource

# Initialize Server
server = Server("stock-data-mcp")

# Define Tools
@server.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="get_current_time",
            description="Get the current system time. Use this to calculate start_date and end_date for queries (e.g. 'last month').",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="query_stock_data",
            description="Query historical data for A-share stocks. Supports fuzzy search by name or code.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Stock name (e.g., '茅台') or code (e.g., '600519')"},
                    "start_date": {"type": "string", "description": "Start date in YYYY-MM-DD format"},
                    "end_date": {"type": "string", "description": "End date in YYYY-MM-DD format"}
                },
                "required": ["query", "start_date", "end_date"]
            }
        ),
        Tool(
            name="query_index_data",
            description="Query historical data for indices (e.g., '上证指数').",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Index name or code"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
                },
                "required": ["query", "start_date", "end_date"]
            }
        ),
        Tool(
            name="query_fund_data",
            description="Query historical data for Funds (ETF preferred).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Fund name or code"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
                },
                "required": ["query", "start_date", "end_date"]
            }
        ),
        Tool(
            name="query_futures_data",
            description="Query historical data for Futures.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Futures symbol (e.g. 'RB')"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
                },
                "required": ["query", "start_date", "end_date"]
            }

        ),
        Tool(
            name="query_hk_stock_data",
            description="Query historical data for Hong Kong stocks. Supports fuzzy search by name or code (5 digits).",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Stock name or code"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
                },
                "required": ["query", "start_date", "end_date"]
            }
        ),
        Tool(
            name="query_us_stock_data",
            description="Query historical data for US stocks. Supports fuzzy search by name (e.g. 'Apple') or code (e.g. 'AAPL').",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Stock name or code"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
                },
                "required": ["query", "start_date", "end_date"]
            }
        ),
        Tool(
            name="query_us_fund_data",
            description="Query historical data for US Funds/ETFs (e.g. 'SPY', 'QQQ').",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Fund name or code"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
                },
                "required": ["query", "start_date", "end_date"]
            }
        ),
        Tool(
            name="query_foreign_futures_data",
            description="Query historical data for Foreign Futures (e.g. 'A50', 'CL').",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Futures symbol"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"}
                },
                "required": ["query", "start_date", "end_date"]
            }
        ),

        Tool(
            name="get_stock_info",
            description="Get detailed information for a specific stock (A-share).",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock code (e.g. '600519')"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_stock_indicators",
            description="Get financial indicators (PE, PB, etc.) for a stock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock code"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_financial_report",
            description="Get detailed financial report abstract (Revenue, Net Profit, etc.) for a stock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock code"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_trading_suggest",
            description="Get simple trading suggestions based on MA and RSI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock code"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_market_zt_pool",
            description="Get A-share Limit-Up (ZhangTing) stock pool for a specific date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date YYYY-MM-DD"}
                },
                "required": ["date"]
            }
        ),
        Tool(
            name="get_market_lhb",
            description="Get Dragon-Tiger List (LongHuBang) statistics for a specific date.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "Date YYYY-MM-DD"}
                },
                "required": ["date"]
            }
        ),
        Tool(
            name="get_market_fund_flow",
            description="Get Sector Fund Flow Ranking (Today).",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_stock_news",
            description="Get latest news for a specific stock.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Stock code"}
                },
                "required": ["symbol"]
            }
        ),
        Tool(
            name="get_global_news",
            description="Get latest global financial news.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Any) -> List[TextContent]:
    if name == "get_current_time":
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")
        today_str = now.strftime("%Y-%m-%d")
        
        # Check if today is a trading day
        is_trading_day = "Unknown"
        try:
            trade_df = ak.tool_trade_date_hist_sina()
            # trade_df columns: trade_date
            trade_df['trade_date'] = pd.to_datetime(trade_df['trade_date']).dt.date
            if now.date() in trade_df['trade_date'].values:
                is_trading_day = "Yes"
            else:
                is_trading_day = "No"
        except:
            pass
            
        return [TextContent(type="text", text=f"Current Time: {now_str}\nIs A-Share Trading Day: {is_trading_day}")]

    elif name == "query_stock_data":
        query = arguments.get("query")
        start = arguments.get("start_date")
        end = arguments.get("end_date")
        
        symbol = DataSource.search_stock(query)
        if not symbol:
            return [TextContent(type="text", text=f"Stock not found for query: {query}")]
        
        data = DataSource.get_stock_data(symbol, start, end)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "query_index_data":
        query = arguments.get("query")
        start = arguments.get("start_date")
        end = arguments.get("end_date")
        
        symbol = DataSource.search_index(query)
        data = DataSource.get_index_data(symbol, start, end)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "query_fund_data":
        query = arguments.get("query")
        start = arguments.get("start_date")
        end = arguments.get("end_date")
        
        symbol = DataSource.search_fund(query)
        if not symbol:
            return [TextContent(type="text", text=f"Fund not found for query: {query}")]
        
        data = DataSource.get_fund_data(symbol, start, end)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "query_futures_data":
        query = arguments.get("query")
        start = arguments.get("start_date")
        end = arguments.get("end_date")
        
        symbol = DataSource.search_futures(query)
        data = DataSource.get_futures_data(symbol, start, end)
        data = DataSource.get_futures_data(symbol, start, end)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "query_hk_stock_data":
        query = arguments.get("query")
        start = arguments.get("start_date")
        end = arguments.get("end_date")
        
        symbol = DataSource.search_hk_stock(query)
        if not symbol:
            return [TextContent(type="text", text=f"HK Stock not found for query: {query}")]
        
        data = DataSource.get_hk_stock_data(symbol, start, end)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "query_us_stock_data":
        query = arguments.get("query")
        start = arguments.get("start_date")
        end = arguments.get("end_date")
        
        symbol = DataSource.search_us_stock(query)
        if not symbol:
            return [TextContent(type="text", text=f"US Stock not found for query: {query}")]
        
        data = DataSource.get_us_stock_data(symbol, start, end)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "query_us_fund_data":
        query = arguments.get("query")
        start = arguments.get("start_date")
        end = arguments.get("end_date")
        
        # Reuse US stock search for ETFs often works, or direct symbol
        symbol = DataSource.search_us_stock(query)
        if not symbol:
             # Fallback to using query as symbol if search fails
             symbol = query
        
        data = DataSource.get_us_fund_data(symbol, start, end)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "query_foreign_futures_data":
        query = arguments.get("query")
        start = arguments.get("start_date")
        end = arguments.get("end_date")
        
        # Foreign futures usually need direct symbol or mapping. 
        # For now, we assume query is the symbol or close to it.
        # We can add a search method later if needed.
        symbol = query 
        
        data = DataSource.get_futures_foreign_data(symbol, start, end)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]



    elif name == "get_stock_info":
        symbol = arguments.get("symbol")
        data = DataSource.get_stock_info(symbol)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "get_stock_indicators":
        symbol = arguments.get("symbol")
        data = DataSource.get_stock_indicators(symbol)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "get_financial_report":
        symbol = arguments.get("symbol")
        data = DataSource.get_financial_report(symbol)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "get_trading_suggest":
        symbol = arguments.get("symbol")
        data = DataSource.get_trading_suggest(symbol)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "get_market_zt_pool":
        date = arguments.get("date")
        data = DataSource.get_stock_zt_pool(date)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "get_market_lhb":
        date = arguments.get("date")
        data = DataSource.get_stock_lhb(date)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "get_market_fund_flow":
        data = DataSource.get_sector_fund_flow()
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "get_stock_news":
        symbol = arguments.get("symbol")
        data = DataSource.get_stock_news(symbol)
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    elif name == "get_global_news":
        data = DataSource.get_global_news()
        return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")

# SSE Server Logic
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
        await server.run(streams[0], streams[1], server.create_initialization_options())

async def handle_messages(request):
    await sse.handle_post_message(request.scope, request.receive, request._send)

starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"])
    ]
)

def main():
    mode = os.environ.get("MCP_MODE", "stdio")
    if mode == "sse":
        uvicorn.run(starlette_app, host="0.0.0.0", port=8000)
    else:
        # Run stdio
        async def run_stdio():
            async with stdio_server() as streams:
                await server.run(streams[0], streams[1], server.create_initialization_options())
        
        asyncio.run(run_stdio())

if __name__ == "__main__":
    main()
