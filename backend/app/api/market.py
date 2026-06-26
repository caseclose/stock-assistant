from __future__ import annotations

from fastapi import APIRouter

from app.core.market import MarketStatus, current_market_state, humanize_countdown

router = APIRouter(prefix="/api/market", tags=["market"])

_LABELS = {
    MarketStatus.PRE_MARKET: ("盘前", "Pre-market"),
    MarketStatus.REGULAR: ("盘中", "Regular"),
    MarketStatus.AFTER_HOURS: ("盘后", "After-hours"),
    MarketStatus.CLOSED: ("休市", "Closed"),
}


@router.get("/status")
def get_market_status():
    st = current_market_state()
    zh, en = _LABELS[st.status]
    delta = st.next_transition - st.now_ny
    return {
        "status": st.status.value,
        "label_zh": zh,
        "label_en": en,
        "is_extended": st.is_extended,
        "is_open": st.is_open,
        "now_ny": st.now_ny.isoformat(),
        "next_transition": st.next_transition.isoformat(),
        "countdown": humanize_countdown(delta),
    }
