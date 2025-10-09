#!/usr/bin/env python3
"""
Test normalization rules to verify that products from different providers
with slightly different naming map to the same normalized name.
"""
import sys
sys.path.insert(0, '.')

from app.utils.text import normalize_text
from app.config.normalization_rules import apply_provider_normalization

print("=" * 80)
print("TEST: Normalization Rules")
print("=" * 80)

# Test cases: products that SHOULD map to the same normalized name
test_cases = [
    {
        "description": "MANGUERA SIN SELLO 44.5mm x 20m - Different formats",
        "products": [
            ("LACAR-AGOSTO", "MANGUERA S/SELLO ROT.30Kg.44.5x20 mts. COMPLETA"),
            ("LACAR-AGOSTO", "MANGUERA S/SELLO 44,5 mm. x 20 mts. COMPLETA"),
            ("LISTA DE PRECIOS INCEN SANIT", "MANGUERA 44.5mm x 20m COMPLETA"),
            ("LISTA DE PRECIOS INCEN SANIT", "MANGUERA 44.5 x 20 m"),
        ],
    },
    {
        "description": "MANGUERA SIN SELLO 63.5mm x 25m - Different formats",
        "products": [
            ("LACAR-AGOSTO", "MANGA S/SELLO 63.5 mm. x 25 mts."),
            ("LACAR-AGOSTO", "MANGA S/SELLO 63,5 mm. x 25 mts."),
            ("LISTA DE PRECIOS INCEN SANIT", "MANGUERA 63.5mm x 25m"),
            ("LISTA DE PRECIOS INCEN SANIT", "MANGA 63.5 x 25"),
        ],
    },
    {
        "description": "GABINETE MANGA 44.5mm SIN PUERTA SIN VIDRIO CON TAPA",
        "products": [
            ("LACAR-AGOSTO", "GAB.MANGA 44,5mm. s/pta. s/vid. c/tapa"),
            ("LACAR-AGOSTO", "GAB.MANGA 44.5mm s/pta s/vid c/tapa"),
            ("LISTA DE PRECIOS INCEN SANIT", "GABINETE MANGA 44.5mm SIN PUERTA SIN VIDRIO CON TAPA"),
            ("LISTA DE PRECIOS INCEN SANIT", "GAB. MANGUERA 44.5 SIN PTA SIN VID CON TAPA"),
        ],
    },
    {
        "description": "VALVULA TIPO TEATRO 2\" x 44.5mm CON TAPA",
        "products": [
            ("LACAR-AGOSTO", "VALVULA TIPO TEATRO 2\"x44,5mm. C/TAPA, V/ALUM."),
            ("LACAR-AGOSTO", "VALVULA TIPO TEATRO 2\" x 44.5mm C/TAPA PLASTICA"),
            ("LISTA DE PRECIOS INCEN SANIT", "VALVULA TIPO TEATRO 2\" x 44.5mm CON TAPA"),
            ("LISTA DE PRECIOS INCEN SANIT", "VALVULA TEATRO 2\" 44.5mm C/TAPA"),
        ],
    },
    {
        "description": "MANGUERA SIN SELLO - ARD ARJET (fractional inches)",
        "products": [
            ("ARD", "MANG ARJET 1 1/2 X 10"),  # ARJET = sin sello
            ("INCEN SANIT", "MANGUERA 1.5 X 10"),
            ("LACAR-AGOSTO", "MANGUERA S/SELLO 1 1/2\" X 10m"),
        ],
    },
    {
        "description": "MANGUERA CON SELLO - ARD RYLJET (fractional inches)",
        "products": [
            ("ARD", "MANG RYLJET 2 1/2 X 15"),  # RYLJET = con sello
            ("INCEN SANIT", "MANGUERA CON SELLO 2.5 X 15"),
            ("LACAR-AGOSTO", "MANGUERA C/SELLO 2 1/2\" X 15m"),
        ],
    },
]

for test in test_cases:
    print(f"\n{'=' * 80}")
    print(f"Test: {test['description']}")
    print('=' * 80)
    
    normalized_names = []
    
    for provider, product_name in test['products']:
        # Step 1: General normalization
        norm = normalize_text(product_name)
        # Step 2: Provider-specific normalization
        norm_final = apply_provider_normalization(norm, provider)
        
        normalized_names.append(norm_final)
        
        print(f"\nProvider: {provider}")
        print(f"Original: {product_name}")
        print(f"After normalize_text(): {norm}")
        print(f"After provider rules: {norm_final}")
    
    # Check if all normalized names are the same
    unique_names = set(normalized_names)
    
    print(f"\n{'=' * 80}")
    if len(unique_names) == 1:
        print("✅ PASS: All products mapped to the same normalized name")
        print(f"   Canonical name: {list(unique_names)[0]}")
    else:
        print("❌ FAIL: Products mapped to DIFFERENT normalized names")
        for i, name in enumerate(unique_names, 1):
            print(f"   {i}. {name}")

print(f"\n{'=' * 80}")
print("TEST COMPLETE")
print("=" * 80)

