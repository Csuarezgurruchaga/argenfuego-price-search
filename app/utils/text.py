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


def compute_final_price(base_price: float, margin_multiplier: float, rounding_strategy: str = "none") -> float:
    candidate = float(base_price) * float(margin_multiplier)
    if rounding_strategy == "none":
        return round(candidate, 2)
    if rounding_strategy == "nearest_10":
        return float(int(round(candidate / 10.0) * 10))
    if rounding_strategy == "ceil_10":
        return float(int(math.ceil(candidate / 10.0) * 10))
    if rounding_strategy == "floor_10":
        return float(int(math.floor(candidate / 10.0) * 10))
    # default fallback
    return round(candidate, 2)


