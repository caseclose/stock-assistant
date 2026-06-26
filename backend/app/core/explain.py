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
    reason_zh: str
    reason_en: str


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
    else:
        zh = f"波动率体制子分 {score:.0f}"
        en = f"Volatility regime sub-score {score:.0f}"
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
    src = "日线结构" if daily_sourced else "当前周期"
    touch_date = lv.last_touch.strftime("%Y-%m-%d") if hasattr(lv.last_touch, "strftime") else str(lv.last_touch)
    reason_zh = (
        f"{src}识别：{kind_zh} ${lv.price:.2f}，强度 {lv.strength:.0f}；"
        f"价格回踩该区间 {lv.touches} 次（{lv.pivots} 个 swing 拐点），"
        f"距现价 {lv.distance_pct:+.2f}%，最近触及 {touch_date}"
    )
    reason_en = (
        f"{src}: {kind_en} at ${lv.price:.2f}, strength {lv.strength:.0f}; "
        f"{lv.touches} range retests ({lv.pivots} pivots), "
        f"{lv.distance_pct:+.2f}% from price, last touch {touch_date}"
    )
    return LevelExplanation(
        price=lv.price,
        kind=lv.kind.value,
        strength=lv.strength,
        touches=lv.touches,
        pivots=lv.pivots,
        distance_pct=lv.distance_pct,
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
