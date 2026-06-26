"""Natural-language explanations for signals and S/R levels (template-based)."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.core.levels import Level, LevelKind
from app.core.signal import ScoreBreakdown, Verdict


@dataclass
class ReasonItem:
    key: str
    score: float
    weight: float
    text_zh: str
    text_en: str


@dataclass
class LevelExplanation:
    price: float
    kind: str
    strength: float
    touches: int
    pivots: int
    distance_pct: float
    source: str
    proximity: str
    flipped: bool
    bounce_rate: float | None
    volume_score: float
    hit_rate: float | None
    ma_aligned: list[str]
    reason_zh: str
    reason_en: str


_SOURCE_ZH = {
    "swing": "摆动结构",
    "volume_poc": "成交量 POC",
    "volume_vah": "价值区上沿 VAH",
    "volume_val": "价值区下沿 VAL",
    "psychological": "心理整数关口",
    "trendline": "趋势线延伸",
    "fib_236": "斐波那契 23.6%",
    "fib_382": "斐波那契 38.2%",
    "fib_500": "斐波那契 50%",
    "fib_618": "斐波那契 61.8%",
    "fib_786": "斐波那契 78.6%",
    "ma_sma20": "SMA20 均线",
    "ma_sma50": "SMA50 均线",
    "ma_sma60": "SMA60 均线",
    "ma_sma120": "SMA120 均线",
    "ma_sma200": "SMA200 均线",
    "ma_ema20": "EMA20 均线",
    "ma_ema50": "EMA50 均线",
}
_SOURCE_EN = {
    "swing": "swing structure",
    "volume_poc": "volume POC",
    "volume_vah": "value-area high",
    "volume_val": "value-area low",
    "psychological": "psychological round number",
    "trendline": "projected trendline",
    "fib_236": "Fibonacci 23.6%",
    "fib_382": "Fibonacci 38.2%",
    "fib_500": "Fibonacci 50%",
    "fib_618": "Fibonacci 61.8%",
    "fib_786": "Fibonacci 78.6%",
    "ma_sma20": "SMA20",
    "ma_sma50": "SMA50",
    "ma_sma60": "SMA60",
    "ma_sma120": "SMA120",
    "ma_sma200": "SMA200",
    "ma_ema20": "EMA20",
    "ma_ema50": "EMA50",
}


_VERDICT_ZH = {
    Verdict.STRONG_BUY: "强烈建议买入",
    Verdict.BUY: "建议买入",
    Verdict.HOLD: "建议观望",
    Verdict.SELL: "建议卖出",
    Verdict.STRONG_SELL: "强烈建议卖出",
}
_VERDICT_EN = {
    Verdict.STRONG_BUY: "Strong buy",
    Verdict.BUY: "Buy",
    Verdict.HOLD: "Hold / wait",
    Verdict.SELL: "Sell",
    Verdict.STRONG_SELL: "Strong sell",
}


def _component_reason(key: str, score: float, row: pd.Series) -> tuple[str, str]:
    if key == "trend":
        ema20, ema50 = row.get("ema20"), row.get("ema50")
        if pd.notna(ema20) and pd.notna(ema50):
            if ema20 > ema50:
                zh = f"趋势偏多：EMA20 ({ema20:.2f}) 高于 EMA50 ({ema50:.2f})，子分 {score:.0f}"
                en = f"Bullish trend: EMA20 above EMA50, sub-score {score:.0f}"
            else:
                zh = f"趋势偏空：EMA20 ({ema20:.2f}) 低于 EMA50 ({ema50:.2f})，子分 {score:.0f}"
                en = f"Bearish trend: EMA20 below EMA50, sub-score {score:.0f}"
        else:
            zh, en = f"趋势中性，子分 {score:.0f}", f"Neutral trend, sub-score {score:.0f}"
    elif key == "momentum":
        rsi = row.get("rsi")
        if pd.notna(rsi):
            zh = f"动量 RSI {rsi:.1f}，子分 {score:.0f}"
            en = f"Momentum RSI {rsi:.1f}, sub-score {score:.0f}"
        else:
            zh, en = f"动量子分 {score:.0f}", f"Momentum sub-score {score:.0f}"
    elif key == "bollinger":
        zh = f"布林带位置子分 {score:.0f}（>50 偏强）"
        en = f"Bollinger position sub-score {score:.0f}"
    elif key == "volume":
        zh = f"成交量/OBV 子分 {score:.0f}"
        en = f"Volume/OBV sub-score {score:.0f}"
    elif key == "position":
        zh = f"价位结构（距强支撑/压力）子分 {score:.0f}（>50 靠近支撑）"
        en = f"Position vs S/R sub-score {score:.0f} (>50 nearer support)"
    elif key == "vol_regime":
        zh = f"波动率体制子分 {score:.0f}"
        en = f"Volatility regime sub-score {score:.0f}"
    else:
        zh = f"{key} 子分 {score:.0f}"
        en = f"{key} sub-score {score:.0f}"
    return zh, en


def _weight_key(key: str) -> str:
    return "vol_regime" if key == "volatility" else key


def explain_verdict(score: ScoreBreakdown, enriched: pd.DataFrame) -> tuple[str, str, list[ReasonItem]]:
    row = enriched.iloc[-1]
    summary_zh = (
        f"{_VERDICT_ZH[score.verdict]}（综合分 {score.composite:.1f}/100）。"
        "以下为各维度贡献，仅供参考，不构成投资建议。"
    )
    summary_en = (
        f"{_VERDICT_EN[score.verdict]} (composite {score.composite:.1f}/100). "
        "Component breakdown below — informational only, not investment advice."
    )
    reasons: list[ReasonItem] = []
    for key, sub in score.components.items():
        w = score.weights.get(_weight_key(key), score.weights.get(key, 0.0))
        zh, en = _component_reason(key, sub, row)
        reasons.append(ReasonItem(key=key, score=round(sub, 1), weight=w, text_zh=zh, text_en=en))
    reasons.sort(key=lambda r: r.score * r.weight, reverse=True)
    return summary_zh, summary_en, reasons


def explain_level(lv: Level, *, daily_sourced: bool) -> LevelExplanation:
    kind_zh = "压力位" if lv.kind is LevelKind.RESISTANCE else "支撑位"
    kind_en = "resistance" if lv.kind is LevelKind.RESISTANCE else "support"
    timeframe = "日线" if daily_sourced else "当前周期"
    prox_zh = "近端" if lv.proximity.value == "near" else "远端"
    prox_en = "near-term" if lv.proximity.value == "near" else "structural"
    src_zh = _SOURCE_ZH.get(lv.source, lv.source)
    src_en = _SOURCE_EN.get(lv.source, lv.source)
    flip_zh = "（原支撑跌破转压力）" if lv.flipped and lv.kind is LevelKind.RESISTANCE else (
        "（原压力突破转支撑）" if lv.flipped else ""
    )
    flip_en = " (flipped from support)" if lv.flipped and lv.kind is LevelKind.RESISTANCE else (
        " (flipped from resistance)" if lv.flipped else ""
    )
    touch_date = lv.last_touch.strftime("%Y-%m-%d") if hasattr(lv.last_touch, "strftime") else str(lv.last_touch)
    bounce_zh = f"，历史守住概率 {lv.bounce_rate:.0f}%" if lv.bounce_rate is not None else ""
    bounce_en = f", historical hold rate {lv.bounce_rate:.0f}%" if lv.bounce_rate is not None else ""
    hit_zh = f"，回测命中率 {lv.hit_rate:.0f}%" if lv.hit_rate is not None else ""
    hit_en = f", backtest hold rate {lv.hit_rate:.0f}%" if lv.hit_rate is not None else ""
    ma_zh = f"，均线汇合 {', '.join(lv.ma_aligned)}" if lv.ma_aligned else ""
    ma_en = f", MA confluence {', '.join(lv.ma_aligned)}" if lv.ma_aligned else ""
    reason_zh = (
        f"{prox_zh}{timeframe}{src_zh}：{kind_zh} ${lv.price:.2f}{flip_zh}，强度 {lv.strength:.0f}；"
        f"回踩 {lv.touches} 次（{lv.pivots} pivot），量能分 {lv.volume_score:.0f}{bounce_zh}{hit_zh}{ma_zh}；"
        f"距现价 {lv.distance_pct:+.2f}%，最近触及 {touch_date}"
    )
    reason_en = (
        f"{prox_en} {src_en} on {timeframe}: {kind_en} ${lv.price:.2f}{flip_en}, strength {lv.strength:.0f}; "
        f"{lv.touches} retests ({lv.pivots} pivots), vol-score {lv.volume_score:.0f}{bounce_en}{hit_en}{ma_en}; "
        f"{lv.distance_pct:+.2f}% from price, last touch {touch_date}"
    )
    return LevelExplanation(
        price=lv.price,
        kind=lv.kind.value,
        strength=lv.strength,
        touches=lv.touches,
        pivots=lv.pivots,
        distance_pct=lv.distance_pct,
        source=lv.source,
        proximity=lv.proximity.value,
        flipped=lv.flipped,
        bounce_rate=lv.bounce_rate,
        volume_score=lv.volume_score,
        hit_rate=lv.hit_rate,
        ma_aligned=list(lv.ma_aligned),
        reason_zh=reason_zh,
        reason_en=reason_en,
    )


MA_FIELDS = [
    ("sma5", "SMA5"),
    ("sma10", "SMA10"),
    ("sma20", "SMA20"),
    ("sma60", "SMA60"),
    ("sma120", "SMA120"),
    ("sma200", "SMA200"),
    ("ema20", "EMA20"),
    ("ema50", "EMA50"),
]


def moving_average_snapshot(enriched: pd.DataFrame) -> list[dict]:
    row = enriched.iloc[-1]
    close = float(row["close"])
    out = []
    for col, name in MA_FIELDS:
        val = row.get(col)
        if val is None or pd.isna(val):
            continue
        v = float(val)
        rel = "above" if close >= v else "below"
        out.append({
            "name": name,
            "value": round(v, 2),
            "relation": rel,
            "distance_pct": round((close / v - 1.0) * 100.0, 2),
        })
    return out
