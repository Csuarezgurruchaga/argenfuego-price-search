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
    
    # Preserve special patterns: convert "s/sello" and "c/sello" to distinct tokens
    # This ensures "manguera s/sello" doesn't match "manguera c/sello"
    value = value.replace("s/sello", "ssello")
    value = value.replace("c/sello", "csello")
    value = value.replace("s/ sello", "ssello")
    value = value.replace("c/ sello", "csello")
    
    value = _non_word_re.sub(" ", value)
    value = _space_re.sub(" ", value)
    return value.strip()


def generate_canonical_name(normalized_name: str) -> str:
    """
    Convert normalized product name into a human-readable canonical name.
    Example: "manguera ssello 445x20" → "Manguera Sin Sello 44.5mm x 20m"
    """
    if not normalized_name:
        return ""

    result = normalized_name

    # 1. Expand abbreviations
    expansions = [
        ("ssello", "sin sello"),
        ("csello", "con sello"),
        ("sinpuerta", "sin puerta"),
        ("conpuerta", "con puerta"),
        ("sinvidrio", "sin vidrio"),
        ("convidrio", "con vidrio"),
        ("sintapa", "sin tapa"),
        ("contapa", "con tapa"),
        ("sinllave", "sin llave"),
        ("conllave", "con llave"),
        ("mataf", "matafuego"),
        ("gab", "gabinete"),
        ("dev", "devanadera"),
        ("valv", "valvula"),
    ]
    for abbr, full in expansions:
        result = re.sub(r'\b' + abbr + r'\b', full, result)

    # 2. Add decimal points to measurements
    # Handle 3-digit numbers that are dimensions (445 → 44.5mm, 635 → 63.5mm)
    def add_decimal(match):
        num = match.group(1)
        # Only add decimal for 3-digit numbers likely to be diameters
        if len(num) == 3:
            return num[:-1] + '.' + num[-1] + 'mm'
        elif len(num) == 2:
            # 2-digit numbers like "15", "20", "25" are lengths in meters
            return num + 'm'
        return num

    # Match standalone numbers (not part of x expressions yet)
    # First pass: handle dimensions before 'x'
    parts = result.split('x')
    if len(parts) >= 2:
        # First part is diameter (e.g., "445")
        diameter_part = parts[0].strip()
        # Find last number in diameter part
        diameter_part = re.sub(r'(\d{2,3})(?![\d.])', lambda m: (m.group(1)[:-1] + '.' + m.group(1)[-1] + 'mm' if len(m.group(1)) == 3 else m.group(1)), diameter_part)

        # Second part is length (e.g., "20")
        length_part = parts[1].strip()
        # Find first number in length part (it's the length)
        length_part = re.sub(r'(\d+)(?![\d.])', lambda m: m.group(1) + 'm', length_part, count=1)

        result = diameter_part + ' x ' + length_part

        # Join remaining parts if any
        if len(parts) > 2:
            result += 'x' + 'x'.join(parts[2:])
    else:
        # No 'x', just add units to numbers
        result = re.sub(r'(\d{3})(?![\d.])', lambda m: m.group(1)[:-1] + '.' + m.group(1)[-1] + 'mm', result)

    # 3. Normalize spacing around 'x'
    result = re.sub(r'\s*x\s*', ' x ', result)

    # 4. Add "para" before certain words
    result = re.sub(r'\bp\s+', 'para ', result)

    # 5. Capitalize first letter of each major word
    # Don't capitalize: de, la, el, y, a, en, para, por, del, al, con, sin
    stopwords = {'de', 'la', 'el', 'y', 'a', 'en', 'para', 'por', 'del', 'al', 'con', 'sin'}
    words = result.split()
    capitalized = []
    for i, word in enumerate(words):
        # Always capitalize first word, or if not a stopword
        if i == 0 or word not in stopwords:
            capitalized.append(word.capitalize())
        else:
            capitalized.append(word)

    result = ' '.join(capitalized)

    # 6. Clean up extra spaces
    result = re.sub(r'\s+', ' ', result).strip()

    return result


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


