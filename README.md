# 股市参考助手 · Stock Assistant

美股看盘参考工具：**信号展示 + 支撑/压力位 + K 线均线**，不下单。核心逻辑移植自 [quant](https://github.com/caseclose/quant)；walk-forward 回测未证明样本外 alpha，**仅供参考，不构成投资建议**。

US equities reference dashboard: composite signal, support/resistance levels, candlestick chart with moving averages. **Informational only — not investment advice.**

## 功能 Features

- 自选列表（SQLite）+ Yahoo 报价（15s 刷新）
- K 线多周期：1m / 5m / 15m / 1H / 1D（Alpaca）
- 主图单路 Alpaca WebSocket 实时推送；其余自选 REST 轮询
- 综合信号（买/卖/观望）+ 分项原因（中/英）
- 支撑/压力位 + 强度与回踩说明
- SMA 5/10/20/60/120/200、EMA 20/50 均线开关

## 快速开始 Quick start

### 1. 环境变量

```bash
cp .env.example .env
# 填入 ALPACA_API_KEY / ALPACA_SECRET_KEY（paper 即可）
```

### 2. 后端

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

自选数据库默认：`~/.stock-assistant/watchlist.db`

### 3. 前端

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev   # http://localhost:3000
```

## API（节选）

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/health` | 健康检查 |
| GET/POST/DELETE | `/api/watchlist` | 自选 CRUD + 报价 |
| GET | `/api/symbols/{symbol}/bars?interval=1H` | OHLCV + 指标 |
| GET | `/api/symbols/{symbol}/analysis?interval=1H` | 信号 + S/R + 原因 |
| POST | `/api/stream/subscribe` | 切换主图 WS |
| WS | `/ws/stream` | 实时 K 线 |

## 测试 Tests

```bash
cd backend && .venv/bin/pytest -q
```

## 免责声明 Disclaimer

本仓库与 quant 项目一致：框架在 60 只美股大市值标的 walk-forward 优化后，**未观察到稳定的样本外 Sharpe 超额**。界面展示的技术信号与支撑/压力位仅供研究参考，请勿作为实盘交易依据。

## 来源 Attribution

`backend/app/core/` 自 [quant](https://github.com/caseclose/quant) 移植（data / indicators / levels / signal），并新增 `explain.py` 模板化原因说明。
