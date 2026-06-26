# 股市参考助手 · Stock Assistant

美股看盘参考工具：**信号展示 + 专业级支撑/压力位 + K 线均线**，不下单。核心逻辑移植自 [quant](https://github.com/caseclose/quant)；walk-forward 回测未证明样本外 alpha，**仅供参考，不构成投资建议**。

US equities reference dashboard: composite signal, trader-grade support/resistance, candlestick chart with moving averages. **Informational only — not investment advice.**

## 功能 Features

### 看盘与数据

- 自选列表（SQLite，最多 20 只）+ Yahoo/Alpaca 报价（盘前盘后默认可用，15s 缓存）
- K 线多周期：1m / 5m / 15m / 1H / 1D（**默认含盘前盘后** bar；可关闭）
- 主图单路 Alpaca WebSocket 实时推送（含 bar 就地更新广播）；其余自选 REST 轮询
- 图表向左拖拽自动分页加载更早历史（`before` + `has_more`）
- 顶部市场状态条（盘前 / 盘中 / 盘后 / 休市 + 倒计时）
- 图表时区切换（美东 / 本地）

### 综合信号

- 买 / 卖 / 观望 + 分项原因（趋势、动量、布林、成交量、波动率、**价位结构**）
- SMA 5/10/20/60/120/200、EMA 20/50 均线开关

### 支撑 / 压力位（交易员级）

日内周期以 **日线结构** 为锚，叠加：

| 来源 | 说明 |
|------|------|
| Swing pivot | 自适应窗口摆动高低点聚类 |
| Volume profile | POC / VAH / VAL |
| Fibonacci | 最近摆动腿的 23.6%–78.6% 回撤 |
| Trendline | 最近两 pivot 投影的水平阻力/支撑 |
| Role flip | 突破后支撑↔阻力角色翻转 |

每条价位附带：强度、回踩次数、来源标签、翻转标记、walk-forward 命中率、MA 共振、中/英说明。

图表叠加：**水平 S/R 线**、**斐波那契虚线**、**对角趋势线**（日线 pivot，端点映射到日内时间轴）。

批量校准脚本 `backend/scripts/calibrate_levels.py` 在 15 只流动性标的上统计各来源命中率，写入 `level_calibration.json` 调节强度权重。

## 快速开始 Quick start

### 1. 环境变量

```bash
cp .env.example .env
# 填入 ALPACA_API_KEY / ALPACA_SECRET_KEY（paper 即可）
```

| 变量 | 说明 |
|------|------|
| `ALPACA_API_KEY` / `ALPACA_SECRET_KEY` | Alpaca 密钥 |
| `ALPACA_BASE_URL` | 交易 API（默认 paper） |
| `ALPACA_DATA_URL` | 可选，覆盖行情 REST/WS 端点 |
| `CORS_ORIGINS` | 前端来源，默认 `http://localhost:3000` |
| `WATCHLIST_DB` | 自选库路径，默认 `~/.stock-assistant/watchlist.db` |

### 2. 后端

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

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
| GET | `/api/market/status` | 美股时段状态与倒计时 |
| GET/POST/DELETE | `/api/watchlist` | 自选 CRUD + 报价 |
| GET | `/api/symbols/{symbol}/bars` | OHLCV + 指标；`limit`≤2000，`before` 分页，`extended_hours` |
| GET | `/api/symbols/{symbol}/analysis` | 信号 + S/R + 趋势线 + 原因 |
| POST | `/api/stream/subscribe` | 切换主图 WS（`extended_hours`） |
| WS | `/ws/stream` | 实时 K 线（30s ping 保活） |

`analysis` 响应除 `levels[]` 外含 `trendlines[]`（对角线段坐标）与 `components.position`（价位结构分项）。

## 测试 Tests

```bash
cd backend && .venv/bin/pytest -q
```

当前覆盖：RTH 过滤、StreamHub 订阅/广播、斐波那契配对、趋势线投影、成交量分布、校准逻辑等（32 tests）。

## 校准 Calibration

```bash
cd backend && .venv/bin/python scripts/calibrate_levels.py
```

在 15 只美股大市值标的上重算各来源 walk-forward 命中率，更新 `app/core/level_calibration.json`。

## 架构要点 Architecture notes

- **RTH**：`app/core/rth.py` 统一 REST 历史与 WS 实时 bar 的盘前盘后过滤（小时线 09:00 起，分钟线 09:30 起）
- **StreamHub**：单槽 Alpaca WS；`asyncio.Lock` 串行 subscribe，先拉 warmup 再切换流（fetch 失败保留旧连接）
- **结构层**：`levels.py` + `volume_profile` / `fibonacci` / `trendlines` / `confluence` / `pivots`

## 免责声明 Disclaimer

本仓库与 quant 项目一致：框架在 60 只美股大市值标的 walk-forward 优化后，**未观察到稳定的样本外 Sharpe 超额**。界面展示的技术信号与支撑/压力位仅供研究参考，请勿作为实盘交易依据。

## 来源 Attribution

`backend/app/core/` 自 [quant](https://github.com/caseclose/quant) 移植（data / indicators / levels / signal），并扩展 `explain.py`、`volume_profile`、`fibonacci`、`trendlines`、`level_backtest` 等模块。
