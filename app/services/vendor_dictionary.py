from typing import Optional
from rapidfuzz import fuzz


# Diccionario fusionado de productos multi-proveedor
DICCIONARIO_FUSIONADO = {
    # CATEGORÍA 1: MANGUERAS
    "MANGUERA_CON_SELLO_1_1/2": {
        "Tipo_Estandar": "Manguera CON SELLO IRAM 1 1/2″ (≈ 38.1 mm)",
        "ARD": {
            "Descripcion_Base": "MANG RYIJET 1 1/2",
            "Codigos_Relevantes": ["48920", "48921", "48922", "48923", "48924"]
        },
        "LACAR": {
            "Descripcion_Base": "MANGUERA C/SELLO 45Kg. 38.1mm",
            "Codigos_Relevantes": ["2215", "2216", "2217", "2218"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 1/2",
            "Codigos_Relevantes": ["MAN.RYL.11215", "MAN.RYL.11220", "MAN.RYL.11225", "MAN.RYL.11230"]
        }
    },
    "MANGUERA_CON_SELLO_1_3/4": {
        "Tipo_Estandar": "Manguera CON SELLO IRAM 1 3/4″ (≈ 44.5 mm)",
        "ARD": {
            "Descripcion_Base": "MANG RYIJET 1 3/4",
            "Codigos_Relevantes": ["48900", "48901", "48902", "48903", "48904"]
        },
        "LACAR": {
            "Descripcion_Base": "MANGUERA C/SELLO 45Kg. 44.5mm",
            "Codigos_Relevantes": ["2220", "2221", "2222", "2223"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 3/4",
            "Codigos_Relevantes": ["MAN.RYL.13415", "MAN.RYL.13420", "MAN.RYL.13425", "MAN.RYL.13430"]
        }
    },
    "MANGUERA_CON_SELLO_2": {
        "Tipo_Estandar": "Manguera CON SELLO IRAM 2″ (≈ 50.8 mm)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "MANGUERA C/SELLO 45Kg. 50.8mm",
            "Codigos_Relevantes": ["2225", "2226", "2227", "2228"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2",
            "Codigos_Relevantes": ["MAN.RYL.20015", "MAN.RYL.20020", "MAN.RYL.20025", "MAN.RYL.20030"]
        }
    },
    "MANGUERA_CON_SELLO_2_1/2": {
        "Tipo_Estandar": "Manguera CON SELLO IRAM 2 1/2″ (≈ 63.5 mm)",
        "ARD": {
            "Descripcion_Base": "MANG RYIJET 2 1/2",
            "Codigos_Relevantes": ["48910", "48911", "48912", "48913", "48914"]
        },
        "LACAR": {
            "Descripcion_Base": "MANGUERA C/SELLO 42Kg. 63.5mm",
            "Codigos_Relevantes": ["2230", "2231", "2232", "2233"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2 1/2",
            "Codigos_Relevantes": ["MAN.RYL.21215", "MAN.RYL.21220", "MAN.RYL.21225", "MAN.RYL.21230"]
        }
    },
    "MANGUERA_SIN_SELLO_1_3/4": {
        "Tipo_Estandar": "Manguera SIN SELLO 1 3/4″ (≈ 44.5 mm)",
        "ARD": {
            "Descripcion_Base": "MANG ARJET 1 3/4",
            "Codigos_Relevantes": ["48905", "48906", "48907", "48908", "48909"]
        },
        "LACAR": {
            "Descripcion_Base": "MANGUERA S/SELLO 30Kg. 44.5mm",
            "Codigos_Relevantes": ["2200", "2201", "2202", "2203"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética ARMTEX con uniones de bronce 1 3/4",
            "Codigos_Relevantes": ["MAN.ARM.13415", "MAN.ARM.13420", "MAN.ARM.13425", "MAN.ARM.13430"]
        }
    },
    "MANGUERA_SIN_SELLO_2_1/2": {
        "Tipo_Estandar": "Manguera SIN SELLO 2 1/2″ (≈ 63.5 mm)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "MANGUERA S/SELLO 63,5 mm",
            "Codigos_Relevantes": ["2210", "2211", "2212", "2213"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética estandar con uniones de bronce 2 1/2",
            "Codigos_Relevantes": ["MAN.SIN.21215", "MAN.SIN.21220", "MAN.SIN.21225", "MAN.SIN.21230"]
        }
    },
    # CATEGORÍA 2: BOQUILLAS
    "BOQUILLA_CHORRO_PLENO_R1": {
        "Tipo_Estandar": "Boquilla chorro pleno R1″ (para lanzas 1 1/2″ a 2″)",
        "ARD": {
            "Descripcion_Base": "BOQ. CH. PLENO 1 1/2",
            "Codigos_Relevantes": ["48670"]
        },
        "LACAR": {
            "Descripcion_Base": "BOQUILLA CHORRO PLENO R1",
            "Codigos_Relevantes": ["0184"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Boquilla bronce chorro pleno 1 1/2",
            "Codigos_Relevantes": ["BOQ.PLE.10000"]
        }
    },
    "BOQUILLA_CHORRO_PLENO_R1_1/2": {
        "Tipo_Estandar": "Boquilla chorro pleno R1 1/2″ (para lanza 2 1/2″)",
        "ARD": {
            "Descripcion_Base": "BOQ. CH. PLENO 2 1/2",
            "Codigos_Relevantes": ["48674"]
        },
        "LACAR": {
            "Descripcion_Base": "BOQUILLA CHORRO PLENO R1,5",
            "Codigos_Relevantes": ["0185"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Boquilla bronce para lanza chorro pleno 2 1/2",
            "Codigos_Relevantes": ["BOQ.PLE.11200"]
        }
    },
    "BOQUILLA_NIEBLA_R1": {
        "Tipo_Estandar": "Boquilla chorro pleno/niebla R1″ (para lanzas 1 1/2″ a 2″)",
        "ARD": {
            "Descripcion_Base": "BOQ. CH. NIEBLA 1 1/2",
            "Codigos_Relevantes": ["48675", "48676"]
        },
        "LACAR": {
            "Descripcion_Base": "BOQUILLA CHORRO PLENO-NIEBLA R1",
            "Codigos_Relevantes": ["0187"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Boquilla bronce regulable chorro pleno y niebla 1 1/2",
            "Codigos_Relevantes": ["BOQ.NIE.10000"]
        }
    },
    "BOQUILLA_NIEBLA_R1_1/2": {
        "Tipo_Estandar": "Boquilla chorro pleno/niebla R1 1/2″ (para lanza 2 1/2″)",
        "ARD": {
            "Descripcion_Base": "BOQ. CH. NIEBLA 2 1/2",
            "Codigos_Relevantes": ["48678"]
        },
        "LACAR": {
            "Descripcion_Base": "BOQUILLA CHORRO PLENO-NIEBLA R1,5",
            "Codigos_Relevantes": ["0188"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Boquilla bronce para lanza chorro regulable chorro pleno y niebla 2 1/2",
            "Codigos_Relevantes": ["BOQ.NIE.11200"]
        }
    },
    "BOQUILLA_CIERRE_LENTO_R1": {
        "Tipo_Estandar": "Boquilla cierre lento R1″ (para lanzas 1 1/2″ a 2″)",
        "ARD": {
            "Descripcion_Base": "BOQ. CIERRE LENTO 1 3/4",
            "Codigos_Relevantes": ["48640"]
        },
        "LACAR": {
            "Descripcion_Base": "BOQUILLA CIERRE LENTO R1",
            "Codigos_Relevantes": ["0186"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Boquilla bronce para lanza chorro regulable cierre lento 1 1/2",
            "Codigos_Relevantes": ["BOQ.LEN.10000"]
        }
    },
    # CATEGORÍA 3: VÁLVULAS Y ACCESORIOS DE BRONCERÍA
    "VALVULA_TIPO_TEATRO_1_1/2": {
        "Tipo_Estandar": "Válvula tipo teatro 1 1/2″ (2″ BSP x 1 1/2″ INC)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "VALVULA TIPO TEATRO 2",
            "Codigos_Relevantes": ["0149", "0149 B"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Válvula tipo teatro de 1 1/2",
            "Codigos_Relevantes": ["VAL.TEA.11200"]
        }
    },
    "VALVULA_TIPO_TEATRO_1_3/4": {
        "Tipo_Estandar": "Válvula tipo teatro 1 3/4″ (2″ BSP x 1 3/4″ INC)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "VALVULA TIPO TEATRO 2",
            "Codigos_Relevantes": ["0150", "0150 B", "0150 C"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Válvula tipo teatro de 1 3/4",
            "Codigos_Relevantes": ["VAL.TEA.13400"]
        }
    },
    "VALVULA_TIPO_TEATRO_2": {
        "Tipo_Estandar": "Válvula tipo teatro 2″ (2″ BSP x 2″ INC)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "VALVULA TIPO TEATRO 2",
            "Codigos_Relevantes": ["0151", "0151 B"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Válvula tipo teatro de 2",
            "Codigos_Relevantes": ["VAL.TEA.20000"]
        }
    },
    "VALVULA_TIPO_TEATRO_2_1/2": {
        "Tipo_Estandar": "Válvula tipo teatro 2 1/2″ (2 1/2″ BSP x 2 1/2″ INC)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "VALVULA TIPO TEATRO 2 1/2",
            "Codigos_Relevantes": ["0152", "0152 B", "0152 BSP"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Válvula tipo teatro de 2 1/2",
            "Codigos_Relevantes": ["VAL.TEA.21200"]
        }
    },
    "BOCA_IMPULSION_2_1/2_SIMPLE": {
        "Tipo_Estandar": "Boca de impulsión simple 2 1/2″ (63.5 mm)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "BOCA DE IMPULSION 2 1/2",
            "Codigos_Relevantes": ["0153"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Válvula de Impulsión para Piso o Pared c/anilla giratoria de 2 1/2",
            "Codigos_Relevantes": ["VAL.IMP.21200", "VAL.IMP.21201"]
        }
    },
    "ANILLA_GIRATORIA_2_1/2": {
        "Tipo_Estandar": "Anilla giratoria 2 1/2″",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "ANILLA GIRATORIA 63.5 mm",
            "Codigos_Relevantes": ["0180"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Anilla giratoria de 2 1/2",
            "Codigos_Relevantes": ["VAL.IMP.21203"]
        }
    },
    "REDUCCION_2_1/2H_A_1_3/4M": {
        "Tipo_Estandar": "Reducción Bronce 2 1/2″ H a 1 3/4″ M",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "REDUCCION 63.5 mm. H - A 44.5 mm. M",
            "Codigos_Relevantes": ["0154"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Reducción de bronce rosca INC-INC 2 1/2",
            "Codigos_Relevantes": ["RED.INC.21213"]
        }
    },
    "LANZA_SIN_BOQUILLA_1_3/4": {
        "Tipo_Estandar": "Lanza sin boquilla 1 3/4″ (≈ 44.5 mm)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "LANZA 44,5 mm. S/BOQUILLA",
            "Codigos_Relevantes": ["0165", "0165 B"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Lanza bronce - aluminio sin boquilla 1 3/4",
            "Codigos_Relevantes": ["LAN.SIN.13400"]
        }
    },
    "LANZA_SIN_BOQUILLA_2": {
        "Tipo_Estandar": "Lanza sin boquilla 2″ (≈ 50.8 mm)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "LANZA 50,8 mm. BRONCE-COBRE S/BOQUILLA",
            "Codigos_Relevantes": ["0166"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Lanza bronce cobre sin boquilla 2",
            "Codigos_Relevantes": ["LAN.SIN.20000"]
        }
    },
    "LANZA_SIN_BOQUILLA_2_1/2": {
        "Tipo_Estandar": "Lanza sin boquilla 2 1/2″ (≈ 63.5 mm)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "LANZA 63,5 mm. BRONCE-COBRE S/BOQUILLA",
            "Codigos_Relevantes": ["0167"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Lanza bronce cobre sin boquilla 2 1/2",
            "Codigos_Relevantes": ["LAN.SIN.21200"]
        }
    },
    "LLAVE_DE_AJUSTAR_UNIONES": {
        "Tipo_Estandar": "Llave de Ajustar Uniones Universal",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "LLAVE AJUSTAR UNION ALUM",
            "Codigos_Relevantes": ["0175 A", "0175 SP"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Llave de ajustar uniones Universal Combinada",
            "Codigos_Relevantes": ["LLA.AJU.00001"]
        }
    },
    # CATEGORÍA 4: GABINETES Y ACCESORIOS DE HERRERÍA
    "GABINETE_MANGUERA_1_3/4": {
        "Tipo_Estandar": "Gabinete para Manguera 1 3/4″ (≈ 44.5 mm)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "GAB.MANGA 44,5mm",
            "Codigos_Relevantes": ["0002", "0002 C", "0002 L", "0532", "0533", "0534", "1311", "1312"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Gabinete para manguera de 1 3/4",
            "Codigos_Relevantes": ["GAB.505516.PA", "GAB.505516.BA", "GAB.505516.G", "GAB.505516.FC", "GAB.505516.FCTX", "GAB.505516.FEAI", "GAB.505516.AI", "GAB.505516.PAI"]
        }
    },
    "GABINETE_MANGUERA_2_1/2": {
        "Tipo_Estandar": "Gabinete para Manguera 2 1/2″ (≈ 63.5 mm)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "GAB.MANGA 63.5mm",
            "Codigos_Relevantes": ["0001", "0001 L", "0501", "0502", "0503", "1301", "1302"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Gabinete para manguera de 2 1/2",
            "Codigos_Relevantes": ["GAB.606520.PA", "GAB.606520.G", "GAB.606520.FC", "GAB.606520.FCTX", "GAB.606520.FEAI", "GAB.606520.AI", "GAB.606520.PAI"]
        }
    },
    "GABINETE_MATAFUEGO_5KG": {
        "Tipo_Estandar": "Gabinete para Matafuego 5kg",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "GAB.MATAF.POLVOx5",
            "Codigos_Relevantes": ["0005", "0005 DUO", "0005 L", "0590", "0591", "0592", "0593", "1331", "1332"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Gabinete para Matafuego de 5 kg. ABC",
            "Codigos_Relevantes": ["GAB.275520.PA", "GAB.275520.G"]
        }
    },
    "GABINETE_MATAFUEGO_10KG": {
        "Tipo_Estandar": "Gabinete para Matafuego 10kg",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "GAB.MATAF.POLVOx10",
            "Codigos_Relevantes": ["0003", "0003 DUO", "0003 L", "0560", "0561", "0562", "0563", "1321", "1322"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Gabinete para Matafuego de 10 kg. ABC",
            "Codigos_Relevantes": ["GAB.337025.PA", "GAB.337025.G"]
        }
    },
    "TAPA_BOCA_IMPULSION_PARED": {
        "Tipo_Estandar": "Tapa para Boca de Impulsión (Pared)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "TAPA P/BOCA IMP. P/FACH",
            "Codigos_Relevantes": ["0092", "0093"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Tapa con inscripción BOMBEROS para pared",
            "Codigos_Relevantes": ["ΤΑΡ.6040.PA", "ΤΑΡ.6040.AI"]
        }
    },
    "TAPA_BOCA_IMPULSION_PISO": {
        "Tipo_Estandar": "Tapa para Boca de Impulsión (Piso)",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "TAPA P/BOCA IMP. P/PISO",
            "Codigos_Relevantes": ["0090", "0091"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Tapa de chapa antideslizante con inscripción BOMBEROS para piso",
            "Codigos_Relevantes": ["TAP.6040.PI"]
        }
    },
    "BALDE_PARA_ARENA": {
        "Tipo_Estandar": "Balde para Arena y Accesorios",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "Balde y Tapa para Arena",
            "Codigos_Relevantes": ["0080", "0081", "0082"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Balde para Arena y Tapa",
            "Codigos_Relevantes": ["BAL.ARE.00001", "BAL.ARE.00002", "BAL.ARE.00003"]
        }
    },
    # CATEGORÍA 5: ROCIADORES / SPRINKLERS
    "SPRINKLER_1/2": {
        "Tipo_Estandar": "Sprinkler / Rociador 1/2″",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "SPRINKLER R1/2",
            "Codigos_Relevantes": ["0132 C", "0132 CP", "0133 C", "0133 CP"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Sprinkler de 1/2",
            "Codigos_Relevantes": ["SPK.UPR.120560", "SPK.PEN.120560", "SPK.LIB.120000", "SPK.PEN.120561", "SPK.PEN.120562"]
        }
    },
    "SPRINKLER_3/4": {
        "Tipo_Estandar": "Sprinkler / Rociador 3/4″",
        "ARD": {"Descripcion_Base": None, "Codigos_Relevantes": []},
        "LACAR": {
            "Descripcion_Base": "SPRINKLER R3/4",
            "Codigos_Relevantes": ["0132 G", "0132 GP", "0133 G", "0133 GP"]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Sprinkler de 3/4",
            "Codigos_Relevantes": ["SPK.UPR.340801", "SPK.PEN.340801"]
        }
    }
}


def normalize_provider_name(provider_name: str) -> str:
    """Normalize provider name for dictionary lookup."""
    normalized = provider_name.upper().strip()
    # Handle variations
    if "LACAR" in normalized:
        return "LACAR"
    elif "INCEN" in normalized or "SANIT" in normalized:
        return "INCEN-SANIT"
    elif "ARD" in normalized:
        return "ARD"
    return provider_name


def find_product_match(provider_name: str, product_name: str, sku: Optional[str]) -> Optional[str]:
    """
    Find matching product in dictionary based on provider, product name, and/or SKU.
    Returns the Tipo_Estandar if a match is found, None otherwise.

    Strategy:
    1. First pass: Try to match by SKU across ALL products (if SKU is provided)
    2. Second pass: Only if no SKU match, try fuzzy matching on product name
    """
    normalized_provider = normalize_provider_name(provider_name)
    product_normalized = product_name.lower().strip()

    # FIRST PASS: Try SKU matching (most reliable)
    if sku and sku.strip():
        sku_clean = sku.strip()
        for product_key, product_data in DICCIONARIO_FUSIONADO.items():
            if normalized_provider not in product_data:
                continue

            provider_data = product_data[normalized_provider]

            # Check if SKU matches
            if sku_clean in provider_data["Codigos_Relevantes"]:
                return product_data["Tipo_Estandar"]

    # SECOND PASS: Only if no SKU match found, try fuzzy matching
    for product_key, product_data in DICCIONARIO_FUSIONADO.items():
        if normalized_provider not in product_data:
            continue

        provider_data = product_data[normalized_provider]

        # Skip if provider has no listing for this product
        if provider_data["Descripcion_Base"] is None:
            continue

        # Check description match with fuzzy matching
        descripcion_base = provider_data["Descripcion_Base"]
        if descripcion_base:
            descripcion_normalized = descripcion_base.lower().strip()

            # Use fuzzy matching with a threshold
            similarity = fuzz.partial_ratio(product_normalized, descripcion_normalized)

            # If similarity is high enough, consider it a match
            if similarity >= 70:
                return product_data["Tipo_Estandar"]

    return None
