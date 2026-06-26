export type GlossaryLang = "zh" | "en";

export type GlossaryEntry = {
  title: Record<GlossaryLang, string>;
  desc: Record<GlossaryLang, string>;
  example: Record<GlossaryLang, string>;
};

export type GlossaryId =
  | "sma"
  | "ema"
  | "sma5"
  | "sma10"
  | "sma20"
  | "sma50"
  | "sma60"
  | "sma120"
  | "sma200"
  | "ema20"
  | "ema50"
  | "ma"
  | "poc"
  | "vah"
  | "val"
  | "swing"
  | "psychological"
  | "trendline"
  | "fib"
  | "resistance"
  | "support"
  | "near"
  | "far"
  | "flipped"
  | "strength"
  | "pivot"
  | "bounce_rate"
  | "hit_rate"
  | "trend"
  | "momentum"
  | "rsi"
  | "bollinger"
  | "volume_signal"
  | "obv"
  | "position"
  | "vol_regime"
  | "composite"
  | "verdict"
  | "extended_hours"
  | "interval"
  | "ma_above"
  | "ma_below"
  | "num_score_scale"
  | "num_sub_score"
  | "num_weight"
  | "num_level_price"
  | "num_touches"
  | "num_pivot_count"
  | "num_volume_score"
  | "num_distance_pct"
  | "num_ma_price"
  | "num_ma_distance_pct"
  | "num_quote_price"
  | "num_change_pct"
  | "num_trendline_end_price"
  | "signal_breakdown";

export const GLOSSARY: Record<GlossaryId, GlossaryEntry> = {
  sma: {
    title: { zh: "SMA 简单移动平均线", en: "SMA (Simple Moving Average)" },
    desc: {
      zh: "过去 N 根 K 线收盘价的算术平均。周期越长越平滑，滞后越大，常作趋势方向与动态支撑/压力。",
      en: "Arithmetic mean of the last N closes. Longer periods are smoother and lag more; often used for trend and dynamic S/R.",
    },
    example: {
      zh: "例：SMA20 上穿 SMA60 常被视为中期转强信号；股价回踩 SMA20 不破，多头有时会继续推进。",
      en: "Ex: SMA20 crossing above SMA60 is often read as medium-term strength; a hold above SMA20 on pullbacks can support continuation.",
    },
  },
  ema: {
    title: { zh: "EMA 指数移动平均线", en: "EMA (Exponential Moving Average)" },
    desc: {
      zh: "对近期价格赋予更高权重的均线，比同周期 SMA 更灵敏，适合短中期趋势与动量判断。",
      en: "Weights recent prices more heavily than SMA of the same length; more responsive for short/medium trend and momentum.",
    },
    example: {
      zh: "例：EMA20 在 EMA50 上方且两者向上发散，常描述为短期多头趋势；跌破 EMA20 可能意味动量减弱。",
      en: "Ex: EMA20 above rising EMA50 suggests short-term uptrend; losing EMA20 can mean momentum is fading.",
    },
  },
  sma5: {
    title: { zh: "SMA5", en: "SMA5" },
    desc: {
      zh: "5 日（或 5 根 K 线）简单均线，极短期平均成本，波动大，多用于日内或超短线参考。",
      en: "5-bar simple average; very short-term mean price, noisy—often used for intraday context.",
    },
    example: {
      zh: "例：1 小时图上 SMA5 向上拐头，可能示意最近几根 K 线买盘偏强，但需结合更大周期。",
      en: "Ex: On a 1H chart, SMA5 turning up can hint at recent buying, but confirm on higher timeframes.",
    },
  },
  sma10: {
    title: { zh: "SMA10", en: "SMA10" },
    desc: {
      zh: "10 根 K 线简单均线，短周期趋势线，介于极短期与短期之间。",
      en: "10-bar SMA; short-term trend line between very fast and standard short MA.",
    },
    example: {
      zh: "例：价格沿 SMA10 震荡上行，跌破后有时会成为短线压力。",
      en: "Ex: Price riding SMA10 higher—once broken, it may act as near-term resistance.",
    },
  },
  sma20: {
    title: { zh: "SMA20", en: "SMA20" },
    desc: {
      zh: "约一个月（日线）或短周期核心均线，机构与散户都常关注，支撑/压力意义较强。",
      en: "~1 month on daily charts; widely watched dynamic support/resistance.",
    },
    example: {
      zh: "例：日线回踩 SMA20 获支撑后反弹，可视为趋势未破坏；有效跌破则警惕转弱。",
      en: "Ex: Daily bounce off SMA20 can keep trend intact; a decisive break may signal weakness.",
    },
  },
  sma50: {
    title: { zh: "SMA50", en: "SMA50" },
    desc: {
      zh: "约 50 根 K 线的简单均线，美股常称「季度线」附近的中期趋势参考。",
      en: "~50-bar SMA; common medium-term trend reference in US equities.",
    },
    example: {
      zh: "例：指数守在 SMA50 上方，中期趋势常被视为未破坏。",
      en: "Ex: Index holding SMA50 often keeps medium-term trend intact.",
    },
  },
  sma60: {
    title: { zh: "SMA60", en: "SMA60" },
    desc: {
      zh: "约一季度均线，中期趋势参考，A 股市场也常以 60 日线衡量牛熊分界之一。",
      en: "~quarterly trend gauge; in some markets, 60-day MA marks medium-term bias.",
    },
    example: {
      zh: "例：股价长期在 SMA60 上方，回调至 SMA60 附近常是中期买点观察区。",
      en: "Ex: Trading above SMA60 with pullbacks to it is a common medium-term buy-watch zone.",
    },
  },
  sma120: {
    title: { zh: "SMA120", en: "SMA120" },
    desc: {
      zh: "约半年均线，过滤短期噪音，识别中期主趋势。",
      en: "~6-month average; filters noise for medium-term trend.",
    },
    example: {
      zh: "例：SMA120 向上且价格在其上方，多描述为中期多头结构。",
      en: "Ex: Price above rising SMA120 often describes a medium-term bullish structure.",
    },
  },
  sma200: {
    title: { zh: "SMA200", en: "SMA200" },
    desc: {
      zh: "约一年均线，美股常用的长期牛熊分界线之一，突破/跌破常引发关注。",
      en: "~1-year MA; classic long-term bull/bear divider in US equities.",
    },
    example: {
      zh: "例：指数重新站上 SMA200 有时被解读为长期趋势修复；下方则偏熊市思维。",
      en: "Ex: Reclaiming SMA200 is sometimes read as long-term repair; below it skews bearish.",
    },
  },
  ema20: {
    title: { zh: "EMA20", en: "EMA20" },
    desc: {
      zh: "短中期指数均线，本工具中常与 EMA50 搭配判断趋势子分。",
      en: "Short/medium EMA; here often paired with EMA50 for the trend score.",
    },
    example: {
      zh: "例：EMA20 > EMA50 且向上，综合信号中「趋势」维度通常偏多。",
      en: "Ex: EMA20 above rising EMA50 usually lifts the trend component score.",
    },
  },
  ema50: {
    title: { zh: "EMA50", en: "EMA50" },
    desc: {
      zh: "稍长周期的指数均线，与 EMA20 构成金叉/死叉类趋势判断。",
      en: "Slightly slower EMA; golden/death cross style checks vs EMA20.",
    },
    example: {
      zh: "例：价格跌破 EMA50 而 EMA20 已下穿 EMA50，可能示意趋势转空。",
      en: "Ex: Price below EMA50 with EMA20 crossing down can mark trend turning bearish.",
    },
  },
  ma: {
    title: { zh: "均线 MA", en: "Moving Average (MA)" },
    desc: {
      zh: "将一段时间内的价格平均后连成线，用于看趋势方向、支撑与压力。",
      en: "Averaged price over time; shows trend direction and dynamic levels.",
    },
    example: {
      zh: "例：收盘价在多条均线之上且均线多头排列，常称「均线多头」。",
      en: "Ex: Close above stacked rising MAs is often called a bullish MA alignment.",
    },
  },
  poc: {
    title: { zh: "POC 成交量控制点", en: "POC (Point of Control)" },
    desc: {
      zh: "成交量分布中成交最密集的价格，代表一段时间内市场认同的「公允价」，常作强支撑/压力。",
      en: "Price with the most traded volume in the profile; market's accepted fair value—strong S/R.",
    },
    example: {
      zh: "例：股价回落到 POC 附近放量反弹，说明该价位买盘承接较强；跌破 POC 可能向下寻找下一密集区。",
      en: "Ex: Bounce at POC on volume shows acceptance; losing POC may seek the next volume node lower.",
    },
  },
  vah: {
    title: { zh: "VAH 价值区上沿", en: "VAH (Value Area High)" },
    desc: {
      zh: "成交量分布价值区（通常约 70% 成交量）的上边界，价格在 VAH 上方常视为偏强。",
      en: "Upper bound of the value area (~70% of volume); trading above VAH skews bullish.",
    },
    example: {
      zh: "例：突破 VAH 后回踩不破，有时被视为多头延续；跌回 VAH 下方则可能回归价值区内震荡。",
      en: "Ex: Breakout above VAH with hold on retest can continue uptrend; back below may mean range trade.",
    },
  },
  val: {
    title: { zh: "VAL 价值区下沿", en: "VAL (Value Area Low)" },
    desc: {
      zh: "价值区下边界，价格在 VAL 下方常视为偏弱；VAL 本身也可作支撑观察。",
      en: "Lower value-area bound; below VAL is weaker; VAL itself can act as support.",
    },
    example: {
      zh: "例：下跌至 VAL 附近缩量企稳，可能示意空头动能衰竭。",
      en: "Ex: Slowing sell volume at VAL can hint sellers are tiring.",
    },
  },
  swing: {
    title: { zh: "摆动高低点", en: "Swing High / Low" },
    desc: {
      zh: "局部显著高点或低点（pivot），连接这些点可识别结构上的支撑与压力。",
      en: "Local pivot highs/lows used to map structural support and resistance.",
    },
    example: {
      zh: "例：连续更高的摆动低点（Higher Lows）是上升趋势的典型结构特征之一。",
      en: "Ex: A series of higher swing lows is a hallmark of an uptrend structure.",
    },
  },
  psychological: {
    title: { zh: "心理整数关口", en: "Psychological Round Number" },
    desc: {
      zh: "如 100、150、200 等整数价位，交易者容易在此挂单，形成自发支撑/压力。",
      en: "Round numbers (100, 200…) where orders cluster, creating natural S/R.",
    },
    example: {
      zh: "例：股价首次冲击 $200 常遇获利盘；有效站上后，$200 可能转为支撑。",
      en: "Ex: First test of $200 often faces profit-taking; a clean break can flip it to support.",
    },
  },
  trendline: {
    title: { zh: "趋势线", en: "Trendline" },
    desc: {
      zh: "连接摆动高点或低点画的斜线，延伸后预测未来可能的阻力或支撑轨迹。",
      en: "Line through swing points, projected forward as sloped S/R.",
    },
    example: {
      zh: "例：上升趋势线被放量跌破，有时意味着短期趋势结束或进入整理。",
      en: "Ex: An uptrend line broken on volume can mark trend pause or reversal.",
    },
  },
  fib: {
    title: { zh: "斐波那契回撤", en: "Fibonacci Retracement" },
    desc: {
      zh: "在一波涨跌后，按 23.6%、38.2%、50%、61.8%、78.6% 等比例划分潜在回撤位。",
      en: "After a swing, ratios like 23.6–78.6% mark potential pullback levels.",
    },
    example: {
      zh: "例：上涨后回踩 38.2% 不破再创新高，常被视为健康回调；跌破 61.8% 则警惕趋势受损。",
      en: "Ex: Holding the 38.2% retrace then new highs is healthy; losing 61.8% warns trend damage.",
    },
  },
  resistance: {
    title: { zh: "压力位", en: "Resistance" },
    desc: {
      zh: "价格上涨时容易遇阻回落的价位区域，卖盘或套牢盘往往集中于此。",
      en: "Price zone where rallies tend to stall due to supply or overhead supply.",
    },
    example: {
      zh: "例：前高 $180 是压力；两次冲高不过形成「双顶」时压力更强。",
      en: "Ex: Prior high at $180 is resistance; a double top strengthens that ceiling.",
    },
  },
  support: {
    title: { zh: "支撑位", en: "Support" },
    desc: {
      zh: "价格下跌时容易获得买盘托底的价位区域。",
      en: "Zone where declines often find buying interest.",
    },
    example: {
      zh: "例：前期平台下沿 $150 曾多次企稳，可作为关键支撑观察。",
      en: "Ex: A shelf at $150 that held multiple times is key support to watch.",
    },
  },
  near: {
    title: { zh: "近端", en: "Near-term" },
    desc: {
      zh: "距当前价 ≤15% 的价位，对当下交易决策更直接相关。",
      en: "Levels within ~15% of current price—most actionable for near-term decisions.",
    },
    example: {
      zh: "例：近端压力 $105、现价 $100，向上空间仅约 5%，短线追涨需谨慎。",
      en: "Ex: Near resistance at $105 with price $100—only ~5% upside; chasing may be risky.",
    },
  },
  far: {
    title: { zh: "远端", en: "Structural / Far" },
    desc: {
      zh: "距现价较远的历史结构位，更多反映长期背景，对短线影响较弱。",
      en: "Distant historical levels—context for bigger picture, less for scalping.",
    },
    example: {
      zh: "例：远端支撑 $80 距现价 $150 很远，短期回调未必能触及，但可作长期防守参考。",
      en: "Ex: Far support at $80 when price is $150—unlikely intraday touch but long-term context.",
    },
  },
  flipped: {
    title: { zh: "支撑/压力翻转", en: "Role Flip (S/R Flip)" },
    desc: {
      zh: "原支撑位被跌破后常转为压力，或原压力被突破后转为支撑（极性转换）。",
      en: "Broken support often becomes resistance and vice versa (polarity flip).",
    },
    example: {
      zh: "例：$50 支撑跌破后反弹至 $50 受阻回落，即「原支撑变压力」。",
      en: "Ex: After losing $50 support, a rally rejected at $50 is a classic flip.",
    },
  },
  strength: {
    title: { zh: "强度", en: "Strength Score" },
    desc: {
      zh: "综合触碰次数、pivot、量能、回测等加权后的 0–100 分，越高表示该价位越「硬」。",
      en: "0–100 blend of touches, pivots, volume, backtest—higher means a tougher level.",
    },
    example: {
      zh: "例：强度 85 的压力位比强度 40 的更值得在策略中优先考虑。",
      en: "Ex: Resistance at strength 85 deserves more weight than one at 40.",
    },
  },
  pivot: {
    title: { zh: "Pivot 转折点", en: "Pivot" },
    desc: {
      zh: "算法识别的局部极值点（高点或低点），是画摆动结构与趋势线的基础。",
      en: "Algorithmic local extrema—building blocks for swings and trendlines.",
    },
    example: {
      zh: "例：某价位关联 3 个 pivot，说明多个转折重合，结构意义更强。",
      en: "Ex: Three pivots at a level mean multiple turns aligned—stronger structure.",
    },
  },
  bounce_rate: {
    title: { zh: "守住率", en: "Hold / Bounce Rate" },
    desc: {
      zh: "历史回测中价格触及该支撑后成功反弹的比例（walk-forward 样本内统计）。",
      en: "Backtest share of support touches that bounced (in-sample walk-forward).",
    },
    example: {
      zh: "例：守住率 70% 表示 10 次触及约 7 次反弹；不代表未来一定有效。",
      en: "Ex: 70% hold rate means ~7/10 bounces historically—not a guarantee forward.",
    },
  },
  hit_rate: {
    title: { zh: "回测命中率", en: "Backtest Hit Rate" },
    desc: {
      zh: "该价位在样本内回测中被验证有效的比例，用于横向比较候选价位质量。",
      en: "In-sample rate the level behaved as expected—compare candidates only.",
    },
    example: {
      zh: "例：两档支撑命中率 65% vs 40%，前者历史表现更一致，但仍需结合现价距离。",
      en: "Ex: 65% vs 40% hit rates—the higher one was more consistent historically.",
    },
  },
  trend: {
    title: { zh: "趋势维度", en: "Trend Component" },
    desc: {
      zh: "综合信号中的趋势子分，主要参考 EMA20 与 EMA50 的相对位置与方向。",
      en: "Composite trend sub-score from EMA20 vs EMA50 alignment.",
    },
    example: {
      zh: "例：趋势子分 75 表示均线结构偏多；子分 <50 则趋势维度拖后腿。",
      en: "Ex: Trend sub-score 75 skews bullish; below 50 drags the composite down.",
    },
  },
  momentum: {
    title: { zh: "动量维度", en: "Momentum Component" },
    desc: {
      zh: "衡量涨跌幅速度与力度，本工具主要用 RSI 等指标量化。",
      en: "Speed/strength of moves—here largely via RSI.",
    },
    example: {
      zh: "例：RSI 从 30 以下回升至 50 上方，动量维度可能从低位修复。",
      en: "Ex: RSI recovering from <30 through 50 can lift the momentum score.",
    },
  },
  rsi: {
    title: { zh: "RSI 相对强弱指数", en: "RSI (Relative Strength Index)" },
    desc: {
      zh: "0–100 振荡指标，>70 常称超买，<30 常称超卖；也可看 50 中轴多空。",
      en: "0–100 oscillator; >70 overbought, <30 oversold; 50 as bull/bear line.",
    },
    example: {
      zh: "例：上升趋势中 RSI 回踩 40–50 不破再起，有时优于在 80 以上追涨。",
      en: "Ex: In uptrends, RSI holding 40–50 on dips can beat chasing above 80.",
    },
  },
  bollinger: {
    title: { zh: "布林带位置", en: "Bollinger Band Position" },
    desc: {
      zh: "收盘价在布林带中的相对位置，靠上轨偏强、靠下轨偏弱，中轨常作均值回归参考。",
      en: "Where close sits inside the bands—upper band strong, lower weak, middle mean-revert.",
    },
    example: {
      zh: "例：沿上轨「_walking the band」是强趋势特征；跌破中轨可能进入整理。",
      en: "Ex: 'Walking the upper band' shows strength; losing the middle band hints consolidation.",
    },
  },
  volume_signal: {
    title: { zh: "成交量维度", en: "Volume Component" },
    desc: {
      zh: "结合放量/缩量与 OBV 等，判断价量是否配合。",
      en: "Price–volume alignment using volume spikes and OBV.",
    },
    example: {
      zh: "例：突破压力位时放量、OBV 创新高，成交量维度通常加分。",
      en: "Ex: Breakout on rising volume with new OBV highs boosts this score.",
    },
  },
  obv: {
    title: { zh: "OBV 能量潮", en: "OBV (On-Balance Volume)" },
    desc: {
      zh: "涨日成交量累加、跌日累减的曲线，用于观察资金流入流出趋势。",
      en: "Cumulative volume signed by up/down days—tracks flow direction.",
    },
    example: {
      zh: "例：股价横盘但 OBV 走高，有时称「隐蔽吸筹」；价涨 OBV 跌则需警惕背离。",
      en: "Ex: Flat price + rising OBV can hint accumulation; price up + OBV down warns divergence.",
    },
  },
  position: {
    title: { zh: "价位结构维度", en: "Position vs S/R" },
    desc: {
      zh: "当前价相对最近强支撑/压力的位置，>50 表示更靠近支撑、下方空间相对大。",
      en: "Where price sits between nearest strong S/R; >50 means closer to support.",
    },
    example: {
      zh: "例：紧贴强支撑反弹，position 子分偏高；顶在强压力下则子分偏低。",
      en: "Ex: Bouncing off strong support lifts position score; pinned under resistance lowers it.",
    },
  },
  vol_regime: {
    title: { zh: "波动率体制", en: "Volatility Regime" },
    desc: {
      zh: "当前波动相对历史是偏高还是偏低，影响止损宽度与突破可信度。",
      en: "Whether volatility is high or low vs history—affects stops and breakout trust.",
    },
    example: {
      zh: "例：低波动收窄后放量突破，有时比高波动乱震中的突破更干净。",
      en: "Ex: Breakouts from low-vol squeezes can be cleaner than ones in chaotic high vol.",
    },
  },
  composite: {
    title: { zh: "综合分", en: "Composite Score" },
    desc: {
      zh: "各维度子分按权重加权后的 0–100 总分，对应买入/观望/卖出等参考标签。",
      en: "Weighted 0–100 blend of components—maps to buy/hold/sell labels.",
    },
    example: {
      zh: "例：综合分 72 可能对应「买入」档，但仍需结合大盘与个人风险承受。",
      en: "Ex: Composite 72 may map to 'Buy'—still weigh market context and risk.",
    },
  },
  verdict: {
    title: { zh: "参考信号", en: "Verdict Label" },
    desc: {
      zh: "由综合分映射的文本标签（强烈买入～强烈卖出），仅作信息展示，非交易指令。",
      en: "Text label from composite (strong buy → strong sell)—informational only.",
    },
    example: {
      zh: "例：「观望」表示多空维度大致均衡，等待更明确结构再行动。",
      en: "Ex: 'Hold' means components are balanced—wait for clearer structure.",
    },
  },
  extended_hours: {
    title: { zh: "盘前盘后", en: "Extended Hours" },
    desc: {
      zh: "包含美股 4:00–9:30（盘前）与 16:00–20:00（盘后）的成交数据，流动性通常弱于正常盘。",
      en: "Includes US pre-market (4:00–9:30 ET) and after-hours (16:00–20:00); thinner liquidity.",
    },
    example: {
      zh: "例：盘后单笔大单可能剧烈波动 K 线，分析时可与「仅正常盘」对比查看。",
      en: "Ex: After-hours prints can spike bars—compare with regular-session-only view.",
    },
  },
  interval: {
    title: { zh: "K 线周期", en: "Chart Interval" },
    desc: {
      zh: "每根 K 线代表的时间跨度；周期越小噪音越多，越大越偏趋势。",
      en: "Time span per bar—smaller = noisier, larger = trend-focused.",
    },
    example: {
      zh: "例：短线看 5 分钟找入场，日线定方向；本工具各周期独立计算指标。",
      en: "Ex: Use 5m for entries, daily for bias—indicators recompute per interval here.",
    },
  },
  ma_above: {
    title: { zh: "价格在均线上方", en: "Price Above MA" },
    desc: {
      zh: "收盘价高于该均线，短期相对强势，该均线常作动态支撑。",
      en: "Close above the MA—relative strength; MA may act as support.",
    },
    example: {
      zh: "例：站在 SMA200 上方常被视为长期多头；回踩不破则趋势延续概率更高。",
      en: "Ex: Above SMA200 is long-term bullish bias; holds on retest support continuation.",
    },
  },
  ma_below: {
    title: { zh: "价格在均线下方", en: "Price Below MA" },
    desc: {
      zh: "收盘价低于该均线，相对弱势，该均线常作动态压力。",
      en: "Close below the MA—relative weakness; MA may cap rallies.",
    },
    example: {
      zh: "例：反弹至 SMA50 下方受阻，说明中期压力仍在。",
      en: "Ex: Rally stalling under SMA50 keeps medium-term pressure in play.",
    },
  },
  num_score_scale: {
    title: { zh: "0–100 分制", en: "0–100 Scale" },
    desc: {
      zh: "本工具中多数评分为 0–100：0 最弱/最空，100 最强/最多。综合分与各维度子分均在此区间。",
      en: "Most scores here are 0–100: 0 weakest/most bearish, 100 strongest/most bullish.",
    },
    example: {
      zh: "例：综合分 65 表示偏多但未极端；子分 40 表示该维度略偏空。",
      en: "Ex: Composite 65 = moderately bullish; a sub-score of 40 = that leg is slightly bearish.",
    },
  },
  num_sub_score: {
    title: { zh: "维度子分", en: "Component Sub-score" },
    desc: {
      zh: "单个信号维度（趋势、动量等）的 0–100 得分，反映该维度当前偏多还是偏空，越高越偏多。",
      en: "0–100 score for one leg (trend, momentum, etc.); higher = more bullish for that leg.",
    },
    example: {
      zh: "例：趋势子分 78、动量子分 45 → 趋势强但动量一般，综合分会被拉向中间。",
      en: "Ex: Trend 78 but momentum 45—strong structure, lukewarm momentum; composite lands in between.",
    },
  },
  num_weight: {
    title: { zh: "综合权重 %", en: "Composite Weight %" },
    desc: {
      zh: "该维度子分在综合分中的占比。贡献 ≈ 子分 × 权重。权重越高，该维度对总分影响越大。",
      en: "Share of the composite from this leg. Contribution ≈ sub-score × weight.",
    },
    example: {
      zh: "例：子分 80、权重 25% → 约贡献 20 分；权重 10% 则同子分只贡献约 8 分。",
      en: "Ex: Sub-score 80 at 25% weight ≈ 20 pts; at 10% weight only ≈ 8 pts.",
    },
  },
  num_level_price: {
    title: { zh: "价位 $", en: "Level Price ($)" },
    desc: {
      zh: "算法识别出的支撑/压力价格（美元），图表上会画水平线；悬停卡片可高亮该线。",
      en: "Algorithmic support/resistance price in USD; shown as a horizontal line on the chart.",
    },
    example: {
      zh: "例：压力 $210 表示价格涨到该附近时，历史曾多次遇阻回落。",
      en: "Ex: Resistance at $210 means price often stalled near that level historically.",
    },
  },
  num_touches: {
    title: { zh: "回踩次数", en: "Touch / Retest Count" },
    desc: {
      zh: "价格历史上触及并测试该价位（进入容差带）的次数，越多说明该价位被市场「认可」越多。",
      en: "How many times price tested this level (within tolerance); more touches = more acceptance.",
    },
    example: {
      zh: "例：支撑 $100 有 8 次回踩 → 比仅 2 次回踩的价位通常更值得关注。",
      en: "Ex: Support at $100 with 8 touches is usually more notable than one with 2.",
    },
  },
  num_pivot_count: {
    title: { zh: "Pivot 个数", en: "Pivot Count" },
    desc: {
      zh: "与该价位关联的摆动转折点数量；多个 pivot 重合表示不同时间的高低点聚在同一价格带。",
      en: "Number of swing pivots tied to this level; more pivots = more structural overlap.",
    },
    example: {
      zh: "例：3 pivots + 6 次回踩 → 结构重合度高，该支撑/压力更「硬」。",
      en: "Ex: 3 pivots plus 6 touches → strong structural overlap at that price.",
    },
  },
  num_volume_score: {
    title: { zh: "量能分 0–100", en: "Volume Score 0–100" },
    desc: {
      zh: "该价位附近历史成交量是否密集：越高表示越多成交堆积在此，价位越像「筹码峰」。",
      en: "How much volume clustered near this price; higher = heavier traded node (volume peak).",
    },
    example: {
      zh: "例：量能分 85 的 POC 价位，通常比量能分 20 的摆动位更有参考价值。",
      en: "Ex: POC with volume score 85 usually matters more than a swing level at 20.",
    },
  },
  num_distance_pct: {
    title: { zh: "距现价 %", en: "Distance from Price %" },
    desc: {
      zh: "该价位相对最新收盘价的百分比距离。正数=在现价上方（压力常见），负数=在下方（支撑常见）。",
      en: "% from latest close. Positive = above price (often resistance); negative = below (support).",
    },
    example: {
      zh: "例：现价 $100，压力 +5% → 约 $105；支撑 -8% → 约 $92。",
      en: "Ex: At $100, +5% resistance ≈ $105; -8% support ≈ $92.",
    },
  },
  num_ma_price: {
    title: { zh: "均线数值 $", en: "MA Value ($)" },
    desc: {
      zh: "按当前 K 线周期计算出的均线最新值（美元），代表近期平均成本。",
      en: "Latest moving-average value in USD for the active chart interval.",
    },
    example: {
      zh: "例：SMA20 = $198.50 表示最近 20 根 K 线均价约在此。",
      en: "Ex: SMA20 = $198.50 means the average close over the last 20 bars.",
    },
  },
  num_ma_distance_pct: {
    title: { zh: "距均线 %", en: "Distance from MA %" },
    desc: {
      zh: "最新收盘价相对该均线的偏离百分比。正=在均线上方，负=在均线下方。",
      en: "% deviation of last close from the MA; positive = above, negative = below.",
    },
    example: {
      zh: "例：+3.2% 表示收盘比均线高约 3.2%；-1% 表示略低于均线。",
      en: "Ex: +3.2% = close ~3.2% above the MA; -1% = slightly below.",
    },
  },
  num_quote_price: {
    title: { zh: "最新价 $", en: "Last Price ($)" },
    desc: {
      zh: "自选列表中的最近成交价（美元），盘前盘后开启时可能含延长时段成交。",
      en: "Latest traded price in USD; may include extended hours when that filter is on.",
    },
    example: {
      zh: "例：$185.20 为当前报价，涨跌幅均相对昨收计算。",
      en: "Ex: $185.20 is the quote; change % is vs prior session close.",
    },
  },
  num_change_pct: {
    title: { zh: "涨跌幅 %", en: "Change %" },
    desc: {
      zh: "相对前一交易日收盘价的涨跌百分比。绿色为正（涨），红色为负（跌）。",
      en: "Percent change vs prior session close. Green = up, red = down.",
    },
    example: {
      zh: "例：+2.35% 表示比昨收高约 2.35%；-0.80% 表示下跌 0.8%。",
      en: "Ex: +2.35% = ~2.35% above yesterday's close; -0.80% = down 0.8%.",
    },
  },
  num_trendline_end_price: {
    title: { zh: "趋势线终点 $", en: "Trendline End Price ($)" },
    desc: {
      zh: "趋势线延伸到当前时刻对应的价格，用于观察斜向支撑/压力在未来附近的位置。",
      en: "Price where the projected trendline sits now—sloped support/resistance.",
    },
    example: {
      zh: "例：支撑斜线终点 $95，现价 $100 → 斜线支撑在下方约 5% 处。",
      en: "Ex: Support line ends at $95 with price $100—sloped support ~5% below.",
    },
  },
  signal_breakdown: {
    title: { zh: "信号分项", en: "Signal Breakdown" },
    desc: {
      zh: "把综合分拆成多个维度，每行左侧为维度名，右侧「子分 × 权重%」表示该维度的得分与占比。",
      en: "Composite split into legs; each row shows name and sub-score × weight %.",
    },
    example: {
      zh: "例：trend 75 × 25% 表示趋势维度偏多且占综合分四分之一权重。",
      en: "Ex: trend 75 × 25% = bullish trend leg with one-quarter of total weight.",
    },
  },
};

const MA_KEY_MAP: Record<string, GlossaryId> = {
  sma5: "sma5",
  sma10: "sma10",
  sma20: "sma20",
  sma50: "sma50",
  sma60: "sma60",
  sma120: "sma120",
  sma200: "sma200",
  ema20: "ema20",
  ema50: "ema50",
  SMA5: "sma5",
  SMA10: "sma10",
  SMA20: "sma20",
  SMA50: "sma50",
  SMA60: "sma60",
  SMA120: "sma120",
  SMA200: "sma200",
  EMA20: "ema20",
  EMA50: "ema50",
};

const SOURCE_MAP: Record<string, GlossaryId> = {
  swing: "swing",
  volume_poc: "poc",
  volume_vah: "vah",
  volume_val: "val",
  psychological: "psychological",
  trendline: "trendline",
  fib_236: "fib",
  fib_382: "fib",
  fib_500: "fib",
  fib_618: "fib",
  fib_786: "fib",
  ma_sma20: "sma20",
  ma_sma50: "sma50",
  ma_sma60: "sma60",
  ma_sma120: "sma120",
  ma_sma200: "sma200",
  ma_ema20: "ema20",
  ma_ema50: "ema50",
};

const SIGNAL_KEY_MAP: Record<string, GlossaryId> = {
  trend: "trend",
  momentum: "momentum",
  bollinger: "bollinger",
  volume: "volume_signal",
  position: "position",
  vol_regime: "vol_regime",
  volatility: "vol_regime",
};

export function getGlossaryEntry(id: GlossaryId): GlossaryEntry | undefined {
  return GLOSSARY[id];
}

export function maGlossaryId(keyOrName: string): GlossaryId {
  return MA_KEY_MAP[keyOrName] ?? "ma";
}

export function sourceGlossaryId(source: string): GlossaryId {
  if (source.startsWith("fib_")) return "fib";
  if (source.startsWith("ma_")) {
    const suffix = source.replace("ma_", "");
    return MA_KEY_MAP[suffix] ?? "ma";
  }
  return SOURCE_MAP[source] ?? "swing";
}

export function signalGlossaryId(key: string): GlossaryId {
  return SIGNAL_KEY_MAP[key] ?? "composite";
}
