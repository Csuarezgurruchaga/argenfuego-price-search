"""
Normalization rules per provider to ensure products from different providers
with slightly different naming conventions map to the same canonical Product.

Each provider can have:
- replacements: List of (pattern, replacement) tuples applied in order
- remove_patterns: List of regex patterns to remove
- defaults: Default values to assume (e.g., if "sello" is not mentioned, assume "sin sello")
"""

import re
from typing import Dict, List, Tuple, Optional


# Provider-specific normalization rules
PROVIDER_RULES: Dict[str, dict] = {
    # LACAR uses: "MANGUERA S/SELLO 44,5 mm. x 20 mts. COMPLETA"
    "LACAR": {
        "replacements": [
            # Normalize decimal separator
            (r"(\d+),(\d+)", r"\1.\2"),  # "44,5" → "44.5"
            
            # Normalize units
            (r"mts\.?", "m"),  # "mts" → "m"
            (r"metros", "m"),
            (r"mm\.?", "mm"),
            
            # Remove spaces around measurements
            (r"(\d+)\s*\.\s*(\d+)", r"\1.\2"),  # "44 . 5" → "44.5"
            (r"(\d+\.?\d*)\s*mm", r"\1mm"),  # "44.5 mm" → "44.5mm"
            (r"(\d+)\s*m\b", r"\1m"),  # "20 m" → "20m"
            
            # Normalize "COMPLETA" marker
            (r"\s*completa?\s*", " completa "),
        ],
        "remove_patterns": [
            r"rot\.?\s*\d+kg\.?",  # Remove "ROT.30Kg"
            r"ø\s*\d+\s*mm\.?",  # Remove diameter markers like "Ø 300 mm."
        ],
    },
    
    # Lista de Precios INCEN SANIT / generic PDF provider
    # Might use: "MANGUERA 44.5mm x 20m" (without "sin sello" mentioned)
    "LISTA DE PRECIOS INCEN SANIT": {
        "replacements": [
            # Normalize decimal separator
            (r"(\d+),(\d+)", r"\1.\2"),
            
            # Normalize units
            (r"mts\.?", "m"),
            (r"metros", "m"),
            (r"mm\.?", "mm"),
            
            # Remove spaces
            (r"(\d+\.?\d*)\s*mm", r"\1mm"),
            (r"(\d+)\s*m\b", r"\1m"),
            (r"(\d+)\s*x\s*(\d+)", r"\1x\2"),  # "44 x 20" → "44x20"
        ],
        "remove_patterns": [],
        "defaults": {
            # If "sello" is not mentioned, assume "sin sello"
            "assume_sin_sello": True,
        },
    },
    
    # Default rules for unknown providers
    "_DEFAULT": {
        "replacements": [
            (r"(\d+),(\d+)", r"\1.\2"),
            (r"mts\.?", "m"),
            (r"metros", "m"),
            (r"(\d+\.?\d*)\s*mm", r"\1mm"),
            (r"(\d+)\s*m\b", r"\1m"),
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
        # BUT ONLY for products that are actually mangueras (not gabinetes, etc.)
        if "sello" not in result:
            # Check if it's SPECIFICALLY a manguera/manga product (not a gabinete, etc.)
            # Look for "manguera" or "manga" followed by measurements (not preceded by "gabinete")
            if re.search(r'\b(manguera|manga)\s+\d', result) and "gabinete" not in result:
                # Insert "ssello" after "manguera/manga"
                result = re.sub(r"\b(manguera|manga)\b", r"\1 ssello", result)
    
    # ========== CANONICAL NORMALIZATION (FINAL PASS) ==========
    # These rules ensure ALL providers map to the same format
    
    # 1. Normalize "manga" → "manguera"
    result = re.sub(r'\bmanga\b', 'manguera', result)
    
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
    
    # 3. Handle inches notation FIRST (before joining digits)
    # Convert "2 " or "2 INCH" to "2in" (normalize_text converted " to INCH in some cases)
    result = re.sub(r'(\d+)\s*inch\b', r'\1in', result, flags=re.IGNORECASE)
    
    # 4. Normalize decimal measurements: "44 5" → "445" (remove space between digits)
    # BUT preserve spaces AFTER inch measurements: "2in 445" should stay as is
    # First, protect inch measurements
    result = re.sub(r'(\d+in)\s+', r'\1 SPACE ', result)
    # Now join other digits
    result = re.sub(r'(\d+)\s+(\d+)', r'\1\2', result)
    # Restore protected spaces
    result = re.sub(r' SPACE ', ' ', result)
    
    # 5. Remove units from measurements
    # Remove "mm" unit (e.g., "445mm" → "445")
    result = re.sub(r'(\d+)mm\b', r'\1', result)
    # Remove "m" unit from lengths (e.g., "20m" → "20")
    result = re.sub(r'(\d+)m\b', r'\1', result)
    
    # 5. Normalize separators
    result = re.sub(r'\s*x\s*', 'x', result)  # "44 x 20" → "44x20"
    result = re.sub(r'\s*de\s*', ' ', result)  # Remove "de" (e.g., "de 1 boca")
    
    # 6. Remove optional/descriptive words that add noise
    noise_words = [r'\bcompleta?\b', r'\balum\b', r'\bplastica?\b', r'\brot\b']
    for word in noise_words:
        result = re.sub(word, '', result, flags=re.IGNORECASE)
    
    # Clean up extra whitespace
    result = re.sub(r'\s+', ' ', result).strip()
    
    return result

