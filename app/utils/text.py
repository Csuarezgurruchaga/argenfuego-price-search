import math
import re
from unidecode import unidecode


_space_re = re.compile(r"\s+")
_non_word_re = re.compile(r"[^\w\s]", re.UNICODE)


def normalize_text(value: str) -> str:
    if value is None:
        return ""
    value = value.strip().lower()
    value = unidecode(value)
    value = _non_word_re.sub(" ", value)
    value = _space_re.sub(" ", value)
    return value.strip()


def compute_final_price(
    base_price: float,
    iva: float = 1.0,
    iibb: float = 1.0,
    profit: float = 1.0,
    margin_multiplier: float = None,  # legacy
    rounding_strategy: str = "none"   # legacy
) -> float:
    """
    Calculate final price with IVA, IIBB, and Profit multipliers.
    Formula: base_price * IVA * IIBB * Profit
    Example: 10 * 1.21 * 1.025 * 2.0 = 24.81
    """
    # If legacy margin_multiplier is provided, use it (backwards compatibility)
    if margin_multiplier is not None:
        candidate = float(base_price) * float(margin_multiplier)
        if rounding_strategy == "none":
            return round(candidate, 2)
        if rounding_strategy == "nearest_10":
            return float(int(round(candidate / 10.0) * 10))
        if rounding_strategy == "ceil_10":
            return float(int(math.ceil(candidate / 10.0) * 10))
        if rounding_strategy == "floor_10":
            return float(int(math.floor(candidate / 10.0) * 10))
        return round(candidate, 2)
    
    # New pricing model
    final = float(base_price) * float(iva) * float(iibb) * float(profit)
    return round(final, 2)


