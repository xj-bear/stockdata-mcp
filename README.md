# 金融数据 MCP 服务器 (Stock Data MCP Server)

这是一个基于 Model Context Protocol (MCP) 的金融数据查询服务器，支持股票、指数、基金和期货的历史数据查询。

## 功能特性

- **功能模块**：
  - **个股深度**：
    - **信息 (Info)**：获取个股详细信息。
    - **指标 (Indicators)**：获取关键财务指标（A股/港股/美股）。
    - **建议 (Suggest)**：基于技术指标（MA, RSI）的简单投资建议。
  - **市场概况**：
    - **涨停/龙虎榜**：获取每日涨停股池及龙虎榜数据。
    - **资金流向**：行业板块资金流向排名。
  - **财经资讯**：
    - **个股新闻**：获取特定股票的新闻。
    - **全球快讯**：获取全球财经快讯（财联社）。
  - **数据查询**：
    - **股票 (Stock)**：支持 A 股、港股、美股的历史数据查询（支持模糊搜索）。
    - **指数 (Index)**：支持常见指数（如 "上证指数"）。
    - **基金 (Fund)**：支持 ETF 和部分基金查询。
    - **期货 (Futures)**：支持国内及外盘期货数据。
- **数据源**：
  - 首选：**东方财富 (Eastmoney)** - 数据最全，但对云环境 IP 限制严格。
  - 备用：**新浪财经 (Sina)** - 当首选接口连接失败时自动切换，确保服务高可用。
- **双模式运行**：
  - **Stdio 模式**：适用于本地 CLI 或 MCP Inspector。
  - **SSE 模式**：适用于 Docker 部署或远程调用。

## 可用工具 (Available Tools)

- **get_current_time**: 获取系统时间。
- **get_stock_info**: 获取个股基本信息 (支持 A/港/美股)。
- **get_stock_indicators**: 获取个股财务指标 (PE/PB/ROE等)。
- **get_financial_report**: 获取个股详细财务报表摘要。
- **get_trading_suggest**: 获取个股简单交易建议。
- **get_stock_zt_pool**: 获取涨停股池。
- **get_stock_lhb**: 获取龙虎榜数据。
- **get_sector_fund_flow**: 获取行业资金流向。
- **get_stock_news**: 获取个股新闻。
- **get_global_news**: 获取全球财经快讯。
- **query_stock_data**: 查询 A 股历史数据 (名称/代码)。
- **query_index_data**: 查询 A 股指数历史数据。
- **query_fund_data**: 查询 A 股基金/ETF 历史数据。
- **query_futures_data**: 查询国内期货历史数据。
- **query_us_stock_data**: 查询美股历史数据 (名称/代码)。
- **query_us_fund_data**: 查询美股基金/ETF 历史数据。
- **query_foreign_futures_data**: 查询外盘期货历史数据。
- **get_hk_stock_data**: 查询港股历史数据。

## 安装与使用

### 1. 本地运行 (Python)

确保已安装 Python 3.10+。

```bash
# 安装依赖
pip install mcp akshare pandas starlette uvicorn httpx

# 运行 (默认 Stdio 模式)
python server.py

# 或者使用 MCP Inspector 测试
npx @modelcontextprotocol/inspector python server.py
```
如果你安装了 Node.js，也可以直接通过 npx 运行（需要本地有 Python 环境）：

```bash
# 在项目根目录下
npm install
npx stockdata-mcp
```

## Cherry Studio 配置指南

本服务器完全支持 **Stdio** 模式，可以直接在 Cherry Studio 中配置使用。

### 配置步骤

1.  打开 Cherry Studio。
2.  进入 **设置 (Settings)** -> **MCP 服务器 (MCP Servers)**。
3.  点击 **添加 (Add)**。
4.  填写以下信息：
    - **名称 (Name)**: Stock Data MCP (或任意名称)
    - **类型 (Type)**: Stdio
    - **命令 (Command)**: `python` (确保 python 在系统 PATH 中，或者使用绝对路径)
    - **参数 (Args)**: 
        - `g:\path\to\stockdata\server.py` (请使用 server.py 的绝对路径)
5.  点击 **保存 (Save)**。
6.  启用该服务器，Cherry Studio 应显示 "Connected" (已连接)。

### 常见问题
- 如果连接失败，请检查 `python` 是否能成功运行 `import akshare`。
- 确保 Cherry Studio 有权限访问该目录。

## 配置文件示例 (Claude Desktop / Cherry Studio)

你可以将以下配置添加到你的 MCP 客户端配置文件中 (如 `claude_desktop_config.json`)。

```json
{
  "mcpServers": {
    "stockdata": {
      "command": "python",
      "args": [
        "g:\\your-disk-path\\stockdata\\server.py"
      ],
      "env": {
        "MCP_MODE": "stdio"
      }
    }
  }
}
```

## 注意事项

- 数据来源于 `akshare`，请确保网络通畅以便连接相关数据接口。
- 模糊搜索可能需要一定时间下载列表，首次运行可能会稍慢。
