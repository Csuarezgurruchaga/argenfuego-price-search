"""
Normalization rules per provider to ensure products from different providers
with slightly different naming conventions map to the same canonical Product.

Each provider can have:
- replacements: List of (pattern, replacement) tuples applied in order
- remove_patterns: List of regex patterns to remove
- defaults: Default values to assume (e.g., if "sello" is not mentioned, assume "sin sello")
"""

import re
from typing import Dict


# Provider-specific normalization rules
PROVIDER_RULES: Dict[str, dict] = {
    # LACAR uses: "MANGUERA S/SELLO 44,5 mm. x 20 mts. COMPLETA"
    # LACAR explicitly specifies "S/SELLO" or "C/SELLO", so no need to assume
    "LACAR": {
        "replacements": [
            # Normalize decimal separator
            (r"(\d+),(\d+)", r"\1.\2"),  # "44,5" → "44.5"
            
            # Normalize units
            (r"mts\.?", "m"),  # "mts" → "m"
            (r"metros", "m"),
            (r"mm\.?", "mm"),
        ],
        "remove_patterns": [
            r"rot\.?\s*\d+kg\.?",  # Remove "ROT.30Kg"
            r"ø\s*\d+\s*mm\.?",  # Remove diameter markers like "Ø 300 mm."
        ],
        # NO assume_sin_sello - LACAR is explicit about s/sello vs c/sello
    },
    
    # INCEN SANIT uses: "MANGUERA 44.5mm x 20m" (without explicit "sin sello")
    # Sometimes uses full text: "MANGUERA CON SELLO" or "MANGUERA SIN SELLO"
    "INCEN SANIT": {
        "replacements": [
            # Normalize explicit sello mentions (before general normalization)
            (r"\bcon sello\b", "csello"),
            (r"\bsin sello\b", "ssello"),
            
            # Normalize decimal separator
            (r"(\d+),(\d+)", r"\1.\2"),
            
            # Normalize units
            (r"mts\.?", "m"),
            (r"metros", "m"),
            (r"mm\.?", "mm"),
        ],
        "remove_patterns": [],
        "defaults": {
            # If "sello" is not mentioned, assume "sin sello"
            "assume_sin_sello": True,
        },
    },
    
    # ARD uses: "MANG RYLJET 1 1/2 X 10" or "MANG ARJET 1 3/4 X 20"
    # - Uses "MANG" instead of "MANGUERA"
    # - Uses fractional inches (1 1/2, 2 1/2, etc.)
    # - Uses brand names to indicate sello type:
    #   * RYLJET = CON SELLO
    #   * ARJET = SIN SELLO
    "ARD": {
        "replacements": [
            # Convert brand names to sello indicators BEFORE removing them
            (r"\bryljet\b", "csello"),  # RYLJET → csello (con sello)
            (r"\barjet\b", "ssello"),   # ARJET → ssello (sin sello)
            
            # Normalize "MANG" → "MANGUERA"
            (r"\bmang\b", "manguera"),
            
            # Normalize decimal separator
            (r"(\d+),(\d+)", r"\1.\2"),
            
            # Normalize units
            (r"mts\.?", "m"),
            (r"metros", "m"),
            (r"mm\.?", "mm"),
        ],
        "remove_patterns": [],  # Don't remove brands - we converted them to sello indicators
        # NO assume_sin_sello - ARD uses brand names to indicate sello type
    },
    
    # Default rules for unknown providers
    "_DEFAULT": {
        "replacements": [
            (r"(\d+),(\d+)", r"\1.\2"),
            (r"mts\.?", "m"),
            (r"metros", "m"),
        ],
        "remove_patterns": [],
        "defaults": {
            "assume_sin_sello": True,
        },
    },
}


def get_provider_rules(provider_name: str) -> dict:
    """
    Get normalization rules for a provider.
    Tries exact match first, then partial match, then default.
    """
    # Exact match
    if provider_name in PROVIDER_RULES:
        return PROVIDER_RULES[provider_name]
    
    # Partial match (e.g., "LACAR-AGOSTO" matches "LACAR")
    for key in PROVIDER_RULES:
        if key != "_DEFAULT" and key.upper() in provider_name.upper():
            return PROVIDER_RULES[key]
    
    # Default
    return PROVIDER_RULES["_DEFAULT"]


def apply_provider_normalization(text: str, provider_name: str) -> str:
    """
    Apply provider-specific normalization rules to text.
    This is applied AFTER the general normalize_text() function.
    """
    rules = get_provider_rules(provider_name)
    result = text.lower()
    
    # Apply replacements in order
    for pattern, replacement in rules.get("replacements", []):
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # Remove unwanted patterns
    for pattern in rules.get("remove_patterns", []):
        result = re.sub(pattern, "", result, flags=re.IGNORECASE)
    
    # Apply defaults
    defaults = rules.get("defaults", {})
    if defaults.get("assume_sin_sello"):
        # If "sello" is not mentioned, add "ssello" to indicate "sin sello"
        # BUT ONLY for standalone manguera products (not gabinetes, válvulas, etc.)
        if "sello" not in result:
            # Check if it's a standalone manguera product
            # Exclude if it's part of "gabinete", "valvula", etc.
            if re.search(r'\b(manguera|manga)\b', result) and not re.search(r'\b(gabinete|gab|valvula|boquilla|columna)\b', result):
                # Check if manguera is followed by measurements or type (not preceded by modifiers)
                if re.search(r'\b(manguera|manga)\s+(\d|ryljet|arjet)', result, re.IGNORECASE):
                    # Insert "ssello" after "manguera/manga"
                    result = re.sub(r"\b(manguera|manga)\b", r"\1 ssello", result, count=1)
    
    # ========== CANONICAL NORMALIZATION (FINAL PASS) ==========
    # These rules ensure ALL providers map to the same format
    
    # 1. Normalize synonyms
    result = re.sub(r'\bmanga\b', 'manguera', result)  # "manga" → "manguera"
    result = re.sub(r'\bboq\b', 'boquilla', result)   # "boq" → "boquilla"
    
    # 2. Normalize abbreviations (common across all providers)
    # Note: normalize_text() already replaced "/" with " ", so "s/pta" becomes "s pta"
    abbreviations = [
        # Handle both "s/pta" (becomes "s pta") and "sin pta" variants
        (r'\bs\s+pta\b', 'sinpuerta'),
        (r'\bsin\s+pta\b', 'sinpuerta'),
        (r'\bsin\s+puerta\b', 'sinpuerta'),
        (r'\bc\s+pta\b', 'conpuerta'),
        (r'\bcon\s+pta\b', 'conpuerta'),
        (r'\bcon\s+puerta\b', 'conpuerta'),
        
        (r'\bs\s+vid\b', 'sinvidrio'),
        (r'\bsin\s+vid\b', 'sinvidrio'),
        (r'\bsin\s+vidrio\b', 'sinvidrio'),
        (r'\bc\s+vid\b', 'convidrio'),
        (r'\bcon\s+vid\b', 'convidrio'),
        (r'\bcon\s+vidrio\b', 'convidrio'),
        
        (r'\bs\s+tapa\b', 'sintapa'),
        (r'\bsin\s+tapa\b', 'sintapa'),
        (r'\bc\s+tapa\b', 'contapa'),
        (r'\bcon\s+tapa\b', 'contapa'),
        
        (r'\bs\s+llave\b', 'sinllave'),
        (r'\bsin\s+llave\b', 'sinllave'),
        (r'\bc\s+llave\b', 'conllave'),
        (r'\bcon\s+llave\b', 'conllave'),
        
        (r'\bp\s+', 'para '),  # "p/" becomes "p "
        (r'\bpara\s+', 'para '),
        (r'\bgab\s+', 'gabinete '),
        (r'\bgabinete\s+', 'gabinete '),
        (r'\bmataf\s+', 'matafuego '),
        (r'\bdev\s+', 'devanadera '),
    ]
    for pattern, replacement in abbreviations:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    # 3. Handle fractional inches (ARD format: "1 1 2" from "1 1/2")
    # Note: normalize_text() already converted "/" to " ", so "1 1/2" → "1 1 2"
    # Convert to decimal WITHOUT decimal point: "1 1 2" → "15" (1.5 → 15 for consistency)
    def convert_fraction(match):
        whole = match.group(1)
        numerator = match.group(2)
        denominator = match.group(3)
        # Handle cases like "1 1 2" (1 + 1/2 = 1.5)
        if denominator in ['2', '4', '8']:  # Common fractions
            decimal = float(whole) + (float(numerator) / float(denominator))
            # Convert to integer-like format: 1.5 → 15, 2.5 → 25
            # This matches the format "44.5" → "445" used elsewhere
            return str(decimal).replace('.', '')
        return match.group(0)  # Return unchanged if not a common fraction
    
    # Match patterns like "1 1 2" that come from "1 1/2"
    result = re.sub(r'\b(\d+)\s+(\d+)\s+(\d+)\b', convert_fraction, result)
    
    # 4. Remove units BEFORE joining digits
    # Remove "mm" unit (e.g., "445 mm" → "445")
    result = re.sub(r'(\d+)\s*mm\b', r'\1', result)
    # Remove "m" unit from lengths (e.g., "20 m" → "20")
    result = re.sub(r'(\d+)\s*m\b', r'\1', result)
    
    # 5. Normalize decimal measurements: "44 5" → "445" (remove space between digits)
    result = re.sub(r'(\d+)\s+(\d+)', r'\1\2', result)
    
    # 6. Normalize separators
    result = re.sub(r'\s*x\s*', 'x', result)  # "44 x 20" → "44x20"
    result = re.sub(r'\s*de\s*', ' ', result)  # Remove "de" (e.g., "de 1 boca")
    
    # 7. Normalize synonyms/variations
    # "tipo teatro" → "teatro" (they're the same product type)
    result = re.sub(r'\btipo\s+teatro\b', 'teatro', result, flags=re.IGNORECASE)
    
    # 8. Remove optional/descriptive words that add noise
    noise_words = [r'\bcompleta?\b', r'\balum\b', r'\bplastica?\b', r'\brot\b', r'\bv\b']
    for word in noise_words:
        result = re.sub(word, '', result, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result

