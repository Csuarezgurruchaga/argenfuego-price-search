from typing import Optional
from rapidfuzz import fuzz

# Diccionario maestro por variantes - cada código SKU es único
DICCIONARIO_MAESTRO_POR_VARIANTES = {
    # =================================================================
    # CATEGORÍA 1: MANGUERAS (ENSAMBLADAS/COMPLETAS)
    # =================================================================
    "MANGUERA_CON_SELLO_1_1/2": {
        "Tipo_Estandar": "Manguera CON SELLO IRAM 1 1/2″ (≈ 38.1 mm)",
        "ARD": {
            "Descripcion_Base": "MANG RYIJET 1 1/2 X [Largo]",
            "Variantes": [
                {"Codigo": "48921", "Descripcion_Completa": "MANG RYIJET 1 1/2 X 15"},
                {"Codigo": "48922", "Descripcion_Completa": "MANG RYIJET 1 1/2 X 20"},
                {"Codigo": "48923", "Descripcion_Completa": "MANG RYIJET 1 1/2 X 25"},
                {"Codigo": "48924", "Descripcion_Completa": "MANG RYIJET 1 1/2 X 30"}
            ]
        },
        "LACAR": {
            "Descripcion_Base": "MANGUERA C/SELLO ROT.45Kg.38.1x[Largo] COMPLETA",
            "Variantes": [
                {"Codigo": "2215", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.38.1x15 COMPLETA"},
                {"Codigo": "2216", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.38.1x20 COMPLETA"},
                {"Codigo": "2217", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.38.1x25 COMPLETA"},
                {"Codigo": "2218", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.38.1x30 COMPLETA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 1/2″ x [Largo]",
            "Variantes": [
                {"Codigo": "MAN.RYL.11215", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 1/2\" x 15 mts."},
                {"Codigo": "MAN.RYL.11220", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 1/2\" x 20 mts."},
                {"Codigo": "MAN.RYL.11225", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 1/2\" x 25 mts."},
                {"Codigo": "MAN.RYL.11230", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 1/2\" x 30 mts."}
            ]
        }
    },
    "MANGUERA_CON_SELLO_1_3/4": {
        "Tipo_Estandar": "Manguera CON SELLO IRAM 1 3/4″ (≈ 44.5 mm)",
        "ARD": {
            "Descripcion_Base": "MANG RYIJET 1 3/4 X [Largo]",
            "Variantes": [
                {"Codigo": "48900", "Descripcion_Completa": "MANG RYIJET 1 3/4 X 10"},
                {"Codigo": "48901", "Descripcion_Completa": "MANG RYIJET 1 3/4 X 15"},
                {"Codigo": "48902", "Descripcion_Completa": "MANG RYIJET 1 3/4 X 20"},
                {"Codigo": "48903", "Descripcion_Completa": "MANG RYIJET 1 3/4 X 25"},
                {"Codigo": "48904", "Descripcion_Completa": "MANG RYIJET 1 3/4 X 30"}
            ]
        },
        "LACAR": {
            "Descripcion_Base": "MANGUERA C/SELLO ROT.45Kg.44.5x[Largo] COMPLETA",
            "Variantes": [
                {"Codigo": "2220", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.44.5x15 COMPLETA"},
                {"Codigo": "2221", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.44.5x20 COMPLETA"},
                {"Codigo": "2222", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.44.5x25 COMPLETA"},
                {"Codigo": "2223", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.44.5x30 COMPLETA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 3/4″ x [Largo]",
            "Variantes": [
                {"Codigo": "MAN.RYL.13415", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 3/4\" x 15 mts."},
                {"Codigo": "MAN.RYL 13420", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 3/4\" x 20 mts."},
                {"Codigo": "MAN.RYL.13425", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 3/4\" x 25 mts."},
                {"Codigo": "MAN.RYL 13430", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 1 3/4\" x 30 mts."}
            ]
        }
    },
    "MANGUERA_CON_SELLO_2": {
        "Tipo_Estandar": "Manguera CON SELLO IRAM 2″ (≈ 50.8 mm)",
        "ARD": { "Descripcion_Base": "No listado.", "Variantes": [] },
        "LACAR": {
            "Descripcion_Base": "MANGUERA C/SELLO ROT.45Kg.50.8x[Largo] COMPLETA",
            "Variantes": [
                {"Codigo": "2225", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.50.8x15 COMPLETA"},
                {"Codigo": "2226", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.50.8x20 COMPLETA"},
                {"Codigo": "2227", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.50.8x25 COMPLETA"},
                {"Codigo": "2228", "Descripcion_Completa": "MANGUERA C/SELLO ROT.45Kg.50.8x30 COMPLETA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2″ x [Largo]",
            "Variantes": [
                {"Codigo": "MAN.RYL.20015", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2\" x 15 mts."},
                {"Codigo": "MAN.RYL.20020", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2\" x 20 mts."},
                {"Codigo": "MAN.RYL.20025", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2\" x 25 mts."},
                {"Codigo": "MAN.RYL.20030", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2\" x 30 mts."}
            ]
        }
    },
    "MANGUERA_CON_SELLO_2_1/2": {
        "Tipo_Estandar": "Manguera CON SELLO IRAM 2 1/2″ (≈ 63.5 mm)",
        "ARD": {
            "Descripcion_Base": "MANG RYIJET 2 1/2 X [Largo]",
            "Variantes": [
                {"Codigo": "48910", "Descripcion_Completa": "MANG RYIJET 2 1/2 X 10"},
                {"Codigo": "48911", "Descripcion_Completa": "MANG RYIJET 2 1/2 X 15"},
                {"Codigo": "48912", "Descripcion_Completa": "MANG RYIJET 2 1/2 X 20"},
                {"Codigo": "48913", "Descripcion_Completa": "MANG RYIJET 2 1/2 X 25"},
                {"Codigo": "48914", "Descripcion_Completa": "MANG RYIJET 2 1/2 X 30"}
            ]
        },
        "LACAR": {
            "Descripcion_Base": "MANGUERA C/SELLO ROT.42Kg.63.5x[Largo] COMPLETA",
            "Variantes": [
                {"Codigo": "2230", "Descripcion_Completa": "MANGUERA C/SELLO ROT.42Kg.63.5x15 COMPLETA"},
                {"Codigo": "2231", "Descripcion_Completa": "MANGUERA C/SELLO ROT.42Kg.63.5x20 COMPLETA"},
                {"Codigo": "2232", "Descripcion_Completa": "MANGUERA C/SELLO ROT.42Kg.63.5x25 COMPLETA"},
                {"Codigo": "2233", "Descripcion_Completa": "MANGUERA C/SELLO ROT.42Kg.63.5x30 COMPLETA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2 1/2″ x [Largo]",
            "Variantes": [
                {"Codigo": "MAN.RYL.21215", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2 1/2\" x 15 mts."},
                {"Codigo": "MAN.RYL.21220", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2 1/2\" x 20 mts."},
                {"Codigo": "MAN.RYL.21225", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2 1/2\" x 25 mts."},
                {"Codigo": "MAN.RYL.21230", "Descripcion_Completa": "Manguera sintética RYL JET sello IRAM con uniones de bronce 2 1/2\" x 30 mts."}
            ]
        }
    },
    "MANGUERA_SIN_SELLO_1_3/4": {
        "Tipo_Estandar": "Manguera SIN SELLO 1 3/4″ (Doble Recubrimiento o Estándar)",
        "ARD": {
            "Descripcion_Base": "MANG ARJET 1 3/4 X [Largo] (Doble Recubrimiento)",
            "Variantes": [
                {"Codigo": "48905", "Descripcion_Completa": "MANG ARJET 1 3/4 X 10"},
                {"Codigo": "48906", "Descripcion_Completa": "MANG ARJET 1 3/4 X 15"},
                {"Codigo": "48907", "Descripcion_Completa": "MANG ARJET 1 3/4 X 20"},
                {"Codigo": "48908", "Descripcion_Completa": "MANG ARJET 1 3/4 X 25"},
                {"Codigo": "48909", "Descripcion_Completa": "MANG ARJET 1 3/4 X 30"}
            ]
        },
        "LACAR": {
            "Descripcion_Base": "MANGUERA S/SELLO 30Kg.44.5x[Largo] COMPLETA (Estándar)",
            "Variantes": [
                {"Codigo": "2200", "Descripcion_Completa": "MANGUERA S/SELLO ROT.30Kg.44.5x15 mts. COMPLETA"},
                {"Codigo": "2201", "Descripcion_Completa": "MANGUERA S/SELLO ROT.30Kg.44.5x20 mts. COMPLETA"},
                {"Codigo": "2202", "Descripcion_Completa": "MANGUERA S/SELLO ROT.30Kg.44.5x25 mts. COMPLETA"},
                {"Codigo": "2203", "Descripcion_Completa": "MANGUERA S/SELLO ROT.30Kg.44.5x30 mts. COMPLETA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Manguera sintética ARMTEX con uniones de bronce 1 3/4″ x [Largo] (Doble Recubrimiento)",
            "Variantes": [
                {"Codigo": "MAN.ARM.13415", "Descripcion_Completa": "Manguera sintética ARMTEX con uniones de bronce 1 3/4\" x 15 mts."},
                {"Codigo": "MAN.ARM.13420", "Descripcion_Completa": "Manguera sintética ARMTEX con uniones de bronce 1 3/4\" x 20 mts."},
                {"Codigo": "MAN.ARM.13425", "Descripcion_Completa": "Manguera sintética ARMTEX con uniones de bronce 1 3/4\" x 25 mts."},
                {"Codigo": "MAN.ARM.13430", "Descripcion_Completa": "Manguera sintética ARMTEX con uniones de bronce 1 3/4\" x 30 mts."}
            ]
        }
    },
    "MANGUERA_SIN_SELLO_2_1/2": {
        "Tipo_Estandar": 'Manguera SIN SELLO 2 1/2" (≈ 63.5 mm)',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": 'MANGUERA S/SELLO 63,5 mm x [Largo] COMPLETA',
            "Variantes": [
                {"Codigo": "2210", "Descripcion_Completa": "MANGUERA S/SELLO 63.5 mm. x 15 mts. COMPLETA"},
                {"Codigo": "2211", "Descripcion_Completa": "MANGUERA S/SELLO 63.5 mm. x 20 mts. COMPLETA"},
                {"Codigo": "2212", "Descripcion_Completa": "MANGUERA S/SELLO 63.5 mm. x 25 mts. COMPLETA"},
                {"Codigo": "2213", "Descripcion_Completa": "MANGUERA S/SELLO 63.5 mm. x 30 mts. COMPLETA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Manguera sintética ARMTEX 2 1/2" x [Largo] c/uniones (Doble Recubrimiento)',
            "Variantes": [
                {"Codigo": "MAN.ARM.21215", "Descripcion_Completa": "Manguera sintética ARMTEX con uniones de bronce 2 1/2\" x 15 mts."},
                {"Codigo": "MAN.ARM.21220", "Descripcion_Completa": "Manguera sintética ARMTEX con uniones de bronce 2 1/2\" x 20 mts."},
                {"Codigo": "MAN.ARM.21225", "Descripcion_Completa": "Manguera sintética ARMTEX con uniones de bronce 2 1/2\" x 25 mts."},
                {"Codigo": "MAN.ARM.21230", "Descripcion_Completa": "Manguera sintética ARMTEX con uniones de bronce 2 1/2\" x 30 mts."}
            ]
        }
    },

    # =================================================================
    # CATEGORÍA 2: BOQUILLAS
    # =================================================================

    "BOQUILLA_CHORRO_PLENO_R1": {
        "Tipo_Estandar": 'Boquilla chorro pleno R1" (para lanzas 1 1/2" a 2")',
        "ARD": {
            "Descripcion_Base": "BOQ. CH. PLENO 1 1/2 Y 1 3/4",
            "Variantes": [{"Codigo": "48670", "Descripcion_Completa": "BOQ. CH. PLENO 1 1/2 Y 1 3/4"}]
        },
        "LACAR": {
            "Descripcion_Base": 'BOQUILLA CHORRO PLENO R1" p/lanza 38.1/44.5/50.8 mm',
            "Variantes": [{"Codigo": "0184", "Descripcion_Completa": "BOQUILLA CHORRO PLENO R1\" PARA LANZA 38.1/44.5/50.8 mm."}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Boquilla bronce chorro pleno 1 1/2" - 1 3/4" - 2"',
            "Variantes": [{"Codigo": "BOQ.PLE.10000", "Descripcion_Completa": "Boquilla bronce para lanza chorro pleno 1 1/2\" - 1 3/4\" - 2\""}]
        }
    },
    "BOQUILLA_CHORRO_PLENO_R1_1/2": {
        "Tipo_Estandar": 'Boquilla chorro pleno R1 1/2" (para lanza 2 1/2")',
        "ARD": {
            "Descripcion_Base": 'BOQ. CH. PLENO 2 1/2"',
            "Variantes": [{"Codigo": "48674", "Descripcion_Completa": "BOQ. CH. PLENO 2 1/2\""}]
        },
        "LACAR": {
            "Descripcion_Base": 'BOQUILLA CHORRO PLENO R1,5" p/lanza 63.5 mm',
            "Variantes": [{"Codigo": "0185", "Descripcion_Completa": "BOQUILLA CHORRO PLENO R1,5\" PARA LANZA 63.5 mm."}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Boquilla bronce para lanza chorro pleno 2 1/2"',
            "Variantes": [{"Codigo": "BOQ.PLE.11200", "Descripcion_Completa": "Boquilla bronce para lanza chorro pleno 2 1/2\""}]
        }
    },
    "BOQUILLA_NIEBLA_R1": {
        "Tipo_Estandar": 'Boquilla chorro pleno/niebla R1" (para lanzas 1 1/2" a 2")',
        "ARD": {
            "Descripcion_Base": 'BOQ. CH. NIEBLA 1 1/2" y 1 3/4"',
            "Variantes": [
                {"Codigo": "48675", "Descripcion_Completa": "BOQ. CH. NIEBLA 1 1/2 Y 1 3/4 TODO BRONCE"},
                {"Codigo": "48676", "Descripcion_Completa": "BOQ. CH. NIEBLA 1 1/2\" Y 1 3/4\" PP"}
            ]
        },
        "LACAR": {
            "Descripcion_Base": 'BOQUILLA CHORRO PLENO-NIEBLA R1" p/lanza 38.1/44.5/50.8 mm',
            "Variantes": [{"Codigo": "0187", "Descripcion_Completa": "BOQUILLA CHORRO PL.-NIEB. R1\" PARA LANZA 38.1/44.5/50.8 mm."}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Boquilla bronce regulable chorro pleno y niebla 1 1/2" - 1 3/4" - 2"',
            "Variantes": [{"Codigo": "BOQ.NIE.10000", "Descripcion_Completa": "Boquilla bronce para lanza chorro regulable chorro pleno y niebla 1 1/2\" - 1 3/4\" - 2\""}]
        }
    },
    "BOQUILLA_NIEBLA_R1_1/2": {
        "Tipo_Estandar": 'Boquilla chorro pleno/niebla R1 1/2" (para lanza 2 1/2")',
        "ARD": {
            "Descripcion_Base": 'BOQ. CH. NIEBLA 2 1/2"',
            "Variantes": [{"Codigo": "48678", "Descripcion_Completa": "BOQ. CH. NIEBLA 2 1/2\""}]
        },
        "LACAR": {
            "Descripcion_Base": 'BOQUILLA CHORRO PLENO-NIEBLA R1,5" p/lanza 63.5 mm',
            "Variantes": [{"Codigo": "0188", "Descripcion_Completa": "BOQUILLA CHORRO PL.-NIEB. R1,5\" PARA LANZA 63.5 mm."}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Boquilla bronce regulable chorro pleno y niebla 2 1/2"',
            "Variantes": [{"Codigo": "BOQ.NIE.11200", "Descripcion_Completa": "Boquilla bronce para lanza chorro regulable chorro pleno y niebla 2 1/2\""}]
        }
    },
    "BOQUILLA_CIERRE_LENTO_R1": {
        "Tipo_Estandar": 'Boquilla cierre lento R1" (para lanzas 1 1/2" a 2")',
        "ARD": {
            "Descripcion_Base": 'BOQ. CIERRE LENTO 1 3/4" o 1 1/2"',
            "Variantes": [{"Codigo": "48640", "Descripcion_Completa": "BOQ. CIERRE LENTO 1 3/4 O 1 1/2"}]
        },
        "LACAR": {
            "Descripcion_Base": 'BOQUILLA CIERRE LENTO R1" p/lanza 38.1/44.5/50.8 mm',
            "Variantes": [{"Codigo": "0186", "Descripcion_Completa": "BOQUILLA CIERRE LENTO R1\" PARA LANZA 38.1/44.5/50.8 mm."}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Boquilla bronce cierre lento 1 1/2" - 1 3/4" - 2"',
            "Variantes": [{"Codigo": "BOQ.LEN.10000", "Descripcion_Completa": "Boquilla bronce para lanza chorro regulable cierre lento 1 1/2\" - 1 3/4\" - 2\""}]
        }
    },

    # =================================================================
    # CATEGORÍA 3: VÁLVULAS Y ACCESORIOS DE BRONCERÍA
    # =================================================================

    "VALVULA_TIPO_TEATRO_1_1/2": {
        "Tipo_Estandar": 'Válvula tipo teatro 1 1/2" (2" BSP x 1 1/2" INC)',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": 'VALVULA TIPO TEATRO 2"x38,1mm.',
            "Variantes": [
                {"Codigo": "0149", "Descripcion_Completa": "VALVULA TIPO TEATRO 2\"x38,1mm. C/TAPA, V/ALUM."},
                {"Codigo": "0149 B", "Descripcion_Completa": "VALVULA TIPO TEATRO 2\"x38,1mm. S/TAPA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Válvula tipo teatro de 1 1/2"',
            "Variantes": [{"Codigo": "VAL.TEA.11200", "Descripcion_Completa": "Válvula tipo teatro de 1 1/2\" 2\"BSP x 1 1/2\"INC"}]
        }
    },
    "VALVULA_TIPO_TEATRO_1_3/4": {
        "Tipo_Estandar": 'Válvula tipo teatro 1 3/4" (2" BSP x 1 3/4" INC)',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": 'VALVULA TIPO TEATRO 2"x44,5mm.',
            "Variantes": [
                {"Codigo": "0150", "Descripcion_Completa": "VALVULA TIPO TEATRO 2\"x44,5mm. C/TAPA, V/ALUM."},
                {"Codigo": "0150 B", "Descripcion_Completa": "VALVULA TIPO TEATRO 2\"x44,5mm. S/TAPA"},
                {"Codigo": "0150 C", "Descripcion_Completa": "VALVULA TIPO TEATRO 2\"x44,5mm. C/TAPA PLASTICA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Válvula tipo teatro de 1 3/4"',
            "Variantes": [{"Codigo": "VAL.TEA.13400", "Descripcion_Completa": "Válvula tipo teatro de 1 3/4\" 2\"BSP x 1 3/4\"INC"}]
        }
    },
    "VALVULA_TIPO_TEATRO_2": {
        "Tipo_Estandar": 'Válvula tipo teatro 2" (2" BSP x 2" INC)',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": [] },
        "LACAR": {
            "Descripcion_Base": 'VALVULA TIPO TEATRO 2"x50,8mm.',
            "Variantes": [
                {"Codigo": "0151", "Descripcion_Completa": "VALVULA TIPO TEATRO 2\"x50,8mm. C/TAPA, V/ALUM."},
                {"Codigo": "0151 B", "Descripcion_Completa": "VALVULA TIPO TEATRO 2\"x50,8mm. S/TAPA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Válvula tipo teatro de 2"',
            "Variantes": [{"Codigo": "VAL.TEA.20000", "Descripcion_Completa": "Válvula tipo teatro de 2\" 2\"BSP x 2\"INC"}]
        }
    },
    "VALVULA_TIPO_TEATRO_2_1/2": {
        "Tipo_Estandar": 'Válvula tipo teatro 2 1/2" (2 1/2" BSP x 2 1/2" INC)',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": 'VALVULA TIPO TEATRO 2 1/2"x63,5mm.',
            "Variantes": [
                {"Codigo": "0152", "Descripcion_Completa": "VALVULA TIPO TEATRO 2 1/2\"x63,5mm. C/TAPA, V/ALUM."},
                {"Codigo": "0152 B", "Descripcion_Completa": "VALVULA TIPO TEATRO 2 1/2\"x63,5mm. S/TAPA"},
                {"Codigo": "0152 BSP", "Descripcion_Completa": "VALVULA TIPO TEATRO 2 1/2\"x63,5mm BSP"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Válvula tipo teatro de 2 1/2"',
            "Variantes": [{"Codigo": "VAL.TEA.21200", "Descripcion_Completa": "Válvula tipo teatro de 2 1/2\" 2 1/2\"BSP x 2 1/2\" INC"}]
        }
    },
    "BOCA_IMPULSION_2_1/2_DOBLE": {
        "Tipo_Estandar": 'Boca de Impulsión Doble 2 1/2"',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": 'BOCA DE IMPULSION DOBLE 63,5 mm.',
            "Variantes": [{"Codigo": "0153 D", "Descripcion_Completa": "BOCA DE IMPULSION DOBLE 63,5 mm."}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Toma de Impulsión doble para Piso de 2 1/2"',
            "Variantes": [{"Codigo": "VAL.IMP.21202", "Descripcion_Completa": "Toma de Impulsión doble para Piso de 2 1/2\""}]
        }
    },
    "ANILLA_GIRATORIA_2_1/2": {
        "Tipo_Estandar": 'Anilla giratoria 2 1/2"',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "ANILLA GIRATORIA 63.5 mm.",
            "Variantes": [{"Codigo": "0180", "Descripcion_Completa": "ANILLA GIRATORIA 63.5 mm."}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Anilla giratoria de 2 1/2"',
            "Variantes": [{"Codigo": "VAL.IMP.21203", "Descripcion_Completa": "Anilla giratoria de 2 1/2\""}]
        }
    },
    "LLAVE_DE_AJUSTAR_UNIONES": {
        "Tipo_Estandar": "Llave de Ajustar Uniones Universal",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "Llave de Ajustar Uniones",
            "Variantes": [
                {"Codigo": "0173", "Descripcion_Completa": "LLAVE DE AJUSTAR STORZ UNIVERSAL"},
                {"Codigo": "0175 A", "Descripcion_Completa": "LLAVE AJUSTAR UNION ALUM. 38,1/63,5 PINTADA"},
                {"Codigo": "0175 SP", "Descripcion_Completa": "LLAVE AJUSTAR UNION ALUM. 38,1/63,5"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Llave de ajustar uniones Universal Combinada",
            "Variantes": [{"Codigo": "LLA.AJU.00001", "Descripcion_Completa": "Llave de ajustar uniones Universal Combinada desde 1 1/2\" a 4\""}]
        }
    },
    "LANZA_SIN_BOQUILLA_1_3/4": {
        "Tipo_Estandar": 'Lanza sin boquilla 1 3/4" (≈ 44.5 mm)',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "LANZA 44,5 mm. S/BOQUILLA",
            "Variantes": [
                {"Codigo": "0165", "Descripcion_Completa": "LANZA 44,5 mm. BRONCE-COBRE S/BOQUILLA"},
                {"Codigo": "0165 B", "Descripcion_Completa": "LANZA 44,5 mm. ALUMINIO S/BOQUILLA"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Lanza bronce - aluminio sin boquilla 1 3/4"',
            "Variantes": [{"Codigo": "LAN.SIN.13400", "Descripcion_Completa": "Lanza bronce - aluminio sin boquilla 1 3/4\""}]
        }
    },
    "LANZA_SIN_BOQUILLA_2": {
        "Tipo_Estandar": 'Lanza sin boquilla 2" (≈ 50.8 mm)',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "LANZA 50,8 mm. BRONCE-COBRE S/BOQUILLA",
            "Variantes": [{"Codigo": "0166", "Descripcion_Completa": "LANZA 50,8 mm. BRONCE-COBRE S/BOQUILLA"}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Lanza bronce cobre sin boquilla 2"',
            "Variantes": [{"Codigo": "LAN.SIN.20000", "Descripcion_Completa": "Lanza bronce cobre sin boquilla 2\""}]
        }
    },
    "LANZA_SIN_BOQUILLA_2_1/2": {
        "Tipo_Estandar": 'Lanza sin boquilla 2 1/2" (≈ 63.5 mm)',
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "LANZA 63,5 mm. BRONCE-COBRE S/BOQUILLA",
            "Variantes": [{"Codigo": "0167", "Descripcion_Completa": "LANZA 63,5 mm. BRONCE-COBRE S/BOQUILLA"}]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": 'Lanza bronce cobre sin boquilla 2 1/2"',
            "Variantes": [{"Codigo": "LAN.SIN.21200", "Descripcion_Completa": "Lanza bronce cobre sin boquilla 2 1/2\""}]
        }
    },

    # =================================================================
    # CATEGORÍA 4: GABINETES Y ACCESORIOS DE HERRERÍA
    # =================================================================

    "GABINETE_MANGUERA_1_3/4": {
        "Tipo_Estandar": "Gabinete para Manguera 1 3/4″ (≈ 44.5 mm)",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "GAB.MANGA 44,5mm.",
            "Variantes": [
                {"Codigo": "0002", "Descripcion_Completa": "GAB.MANGA 44,5mm. s/pta. s/vid. c/tapa"},
                {"Codigo": "0002 C", "Descripcion_Completa": "GAB.MANGA 44,5mm. c/pta. s/vid. p/Columna"},
                {"Codigo": "0002 L", "Descripcion_Completa": "GAB.MANGA 44,5mm. c/pta. s/vid. c/llave"},
                {"Codigo": "0532", "Descripcion_Completa": "GAB.MANGA 44.5mm. C/PTA ENTERIZA Y VISOR"},
                {"Codigo": "0533", "Descripcion_Completa": "GAB.MANGA 44.5mm. C/PTA. P/VIDRIO, C/ALERO"},
                {"Codigo": "1311", "Descripcion_Completa": "GAB.MANGA 44.5mm. C/PTA. EN AC. INOX."},
                {"Codigo": "1312", "Descripcion_Completa": "GAB.MANGA 44.5mm. COMPL.EN AC.INOX. C/PTA."}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Gabinete para manguera de 1 3/4″ (500x550x160 mm)",
            "Variantes": [
                {"Codigo": "GAB.505516.PA", "Descripcion_Completa": "Gabinete para manguera de 1 3/4\" con puerta hierro angulos/vidrio"},
                {"Codigo": "GAB.505516.BA", "Descripcion_Completa": "Gabinete para manguera de 1 3/4\" con puerta plegada Linea Base - s/vidrio"},
                {"Codigo": "GAB.505516.G", "Descripcion_Completa": "Gabinete para manguera de 1 3/4\" cierre tipo guillotina - s/vidrio"},
                {"Codigo": "GAB.505516.FC", "Descripcion_Completa": "Gabinete para manguera de 1 3/4\" con puerta de chapa y visor 10x10 cm s/vidrio"},
                {"Codigo": "GAB.505516.FEAI", "Descripcion_Completa": "Gabinete para manguera de 1 3/4\" con frente estructural de Acero Inoxidable - s/vidrio"},
                {"Codigo": "GAB.505516.AI", "Descripcion_Completa": "Gabinete de Acero Inoxidable para manguera de 1 3/4\" con puerta angulos/vidrio"}
            ]
        }
    },
    "GABINETE_MANGUERA_2_1/2": {
        "Tipo_Estandar": "Gabinete para Manguera 2 1/2″ (≈ 63.5 mm)",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "GAB.MANGA 63.5mm.",
            "Variantes": [
                {"Codigo": "0001", "Descripcion_Completa": "GAB.MANGA 63.5mm. s/pta. s/vid.c/tapa"},
                {"Codigo": "0001 L", "Descripcion_Completa": "GAB.MANGA 63.5mm. c/pta. s/vid. c/llave"},
                {"Codigo": "0501", "Descripcion_Completa": "GAB.MANGA 63.5mm. C/PTA ENTERIZA Y VISOR"},
                {"Codigo": "0502", "Descripcion_Completa": "GAB.MANGA 63.5mm. C/PTA. P/VIDRIO, C/ALERO"},
                {"Codigo": "1301", "Descripcion_Completa": "GAB.MANGA 63.5mm. C/PTA.EN AC. INOX."},
                {"Codigo": "1302", "Descripcion_Completa": "GAB.MANGA 63.5mm. COMPL.EN AC INOX. C/PTA."}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Gabinete para manguera de 2 1/2″ (600x650x200 mm)",
            "Variantes": [
                {"Codigo": "GAB.606520.PA", "Descripcion_Completa": "Gabinete para manguera de 2 1/2\" con puerta hierro angulo - s/vidrio"},
                {"Codigo": "GAB.606520.G", "Descripcion_Completa": "Gabinete para manguera de 2 1/2\" cierre tipo guillotina s/vidrio"},
                {"Codigo": "GAB.606520.FC", "Descripcion_Completa": "Gabinete para manguera de 2 1/2\" con puerta de chapa y visor 10x10 cm - s/vidrio"},
                {"Codigo": "GAB.606520.FEAI", "Descripcion_Completa": "Gabinete para manguera de 2 1/2\" con frente estructural de Acero Inoxidable - s/vidrio"},
                {"Codigo": "GAB.606520.AI", "Descripcion_Completa": "Gabinete de Acero Inoxidable para manguera de 2 1/2\" con puerta angulo - s/vidrio"}
            ]
        }
    },
    "GABINETE_MATAFUEGO_5KG": {
        "Tipo_Estandar": "Gabinete para Matafuego 5kg",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "GAB.MATAF.POLVOx5",
            "Variantes": [
                {"Codigo": "0005", "Descripcion_Completa": "GAB.MATAF.POLVOx5 s/pta. s/vid. c/tapa"},
                {"Codigo": "0005 DUO", "Descripcion_Completa": "GAB.MATAF.POLVOx5 s/pta. s/vid. P/Cand-Torn"},
                {"Codigo": "0005 L", "Descripcion_Completa": "GAB.MATAF.POLVOx5 c/pta. s/vid. c/llave"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Gabinete para Matafuego de 5 kg. ABC",
            "Variantes": [
                {"Codigo": "GAB.275520.PA", "Descripcion_Completa": "Gabinete para Matafuego de 5 kg. ABC con puerta hierro angulo - s/vidrio"},
                {"Codigo": "GAB.275520.G", "Descripcion_Completa": "Gabinete para Matafuego de 5 kg. ABC cierre tipo guillotina - s/vidrio"}
            ]
        }
    },
    "GABINETE_MATAFUEGO_10KG": {
        "Tipo_Estandar": "Gabinete para Matafuego 10kg",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "GAB.MATAF.POLVOx10",
            "Variantes": [
                {"Codigo": "0003", "Descripcion_Completa": "GAB.MATAF.POLVOx10 s/pta. s/vid. c/tapa"},
                {"Codigo": "0003 DUO", "Descripcion_Completa": "GAB.MATAF.POLVOx10 s/pta. s/vid. P/Cand-Torn"},
                {"Codigo": "0003 L", "Descripcion_Completa": "GAB.MATAF.POLVOx10 c/pta. s/vid. c/llave"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Gabinete para Matafuego de 10 kg. ABC",
            "Variantes": [
                {"Codigo": "GAB.337025.PA", "Descripcion_Completa": "Gabinete para Matafuego de 10 kg. ABC con puerta hierro angulo - s/vidrio"},
                {"Codigo": "GAB.337025.G", "Descripcion_Completa": "Gabinete para Matafuego de 10 kg. ABC cierre tipo guillotina - s/vidrio"}
            ]
        }
    },
    "TAPA_BOCA_IMPULSION_PARED": {
        "Tipo_Estandar": "Tapa para Boca de Impulsión (Pared)",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "TAPA P/BOCA IMP. P/FACH",
            "Variantes": [
                {"Codigo": "0092", "Descripcion_Completa": "TAPA P/BOCA IMP.400x600 P/FACH"},
                {"Codigo": "0093", "Descripcion_Completa": "TAPA P/BOCA IMP.600x600 P/FACH"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Tapa con inscripción BOMBEROS para pared",
            "Variantes": [
                {"Codigo": "ΤΑΡ.6040.PA", "Descripcion_Completa": "Tapa con inscripción \"BOMBEROS\" para pared"},
                {"Codigo": "ΤΑΡ.6040.AI", "Descripcion_Completa": "Tapa de acero inoxidable con inscripción \"BOMBEROS\" para pared"}
            ]
        }
    },
    "TAPA_BOCA_IMPULSION_PISO": {
        "Tipo_Estandar": "Tapa para Boca de Impulsión (Piso)",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "TAPA P/BOCA IMP. P/PISO",
            "Variantes": [
                {"Codigo": "0090", "Descripcion_Completa": "TAPA P/BOCA IMP.400x600 P/PISO"},
                {"Codigo": "0091", "Descripcion_Completa": "TAPA P/BOCA IMP.600x600 P/PISO"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Tapa de chapa antideslizante con inscripción BOMBEROS para piso",
            "Variantes": [{"Codigo": "TAP.6040.PI", "Descripcion_Completa": "Tapa de chapa antideslizante 1/8\" (3,175 mm) con inscripción \"BOMBEROS\" para piso"}]
        }
    },
    "BALDE_PARA_ARENA": {
        "Tipo_Estandar": "Balde para Arena y Accesorios",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "Balde y Tapa para Arena",
            "Variantes": [
                {"Codigo": "0080", "Descripcion_Completa": "BALDE MANIJA FIJA CON GRAPA"},
                {"Codigo": "0081", "Descripcion_Completa": "BALDE MANIJA MOVIL CON GRAPA"},
                {"Codigo": "0082", "Descripcion_Completa": "TAPA DE BALDE"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Balde para Arena y Tapa",
            "Variantes": [
                {"Codigo": "BAL.ARE.00001", "Descripcion_Completa": "Balde Manija fija con soporte"},
                {"Codigo": "BAL.ARE.00002", "Descripcion_Completa": "Balde Manija movil con soporte"},
                {"Codigo": "BAL.ARE.00003", "Descripcion_Completa": "Tapa para Balde"}
            ]
        }
    },

    # =================================================================
    # CATEGORÍA 5: ROCIADORES / SPRINKLERS
    # =================================================================
    
    "SPRINKLER_PENDENT_1/2": {
        "Tipo_Estandar": "Sprinkler Pendent 1/2″ K5.6",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "SPRINKLER PENDIENTE R1/2\" K5,6",
            "Variantes": [
                {"Codigo": "0133 C", "Descripcion_Completa": "SPRINKLER PENDIENTE UL-FM R1/2\" K5,6 T68º"},
                {"Codigo": "0133 CP", "Descripcion_Completa": "SPRINKLER PENDIENTE R1/2\" K5,6 T68º"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Sprinkler de 1/2\" Pendent K=5,6",
            "Variantes": [
                {"Codigo": "SPK.PEN.120560", "Descripcion_Completa": "Sprinkler de 1/2\" Pendent K=5,6 con fusible ampolla a 68°C sello ULFM-"},
                {"Codigo": "SPK.PEN.120561", "Descripcion_Completa": "Sprinkler de 1/2\" Pendent K=5,6 con fusible metálico a 74°C sello UL-FM"},
                {"Codigo": "SPK.PEN.120562", "Descripcion_Completa": "Sprinkler de 1/2\" Pendent K=5,6 fusible ampolla a 68°C UL-FM Blanco o cromado"}
            ]
        }
    },
    "SPRINKLER_UPRIGHT_1/2": {
        "Tipo_Estandar": "Sprinkler Upright 1/2″ K5.6",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "SPRINKLER MONTANTE R1/2\" K5,6",
            "Variantes": [
                {"Codigo": "0132 C", "Descripcion_Completa": "SPRINKLER MONTANTE UL-FM R1/2\" K5,6 T68º"},
                {"Codigo": "0132 CP", "Descripcion_Completa": "SPRINKLER MONTANTE R1/2\" K 5,6 T68º"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Sprinkler de 1/2\" Up-Right K=5,6",
            "Variantes": [{"Codigo": "SPK.UPR.120560", "Descripcion_Completa": "Sprinkler de 1/2\" Up-Right K=5,6 con fusible ampolla a 68°C sello ULFM-"}]
        }
    },
    "SPRINKLER_3/4": {
        "Tipo_Estandar": "Sprinkler / Rociador 3/4″",
        "ARD": {"Descripcion_Base": "No listado.", "Variantes": []},
        "LACAR": {
            "Descripcion_Base": "SPRINKLER R3/4\" K8,1",
            "Variantes": [
                {"Codigo": "0132 G", "Descripcion_Completa": "SPRINKLER MONTANTE UL-FM R3/4\" K8,1 T68º"},
                {"Codigo": "0132 GP", "Descripcion_Completa": "SPRINKLER MONTANTE R3/4\" K8,1 T68º"},
                {"Codigo": "0133 G", "Descripcion_Completa": "SPRINKLER PENDIENTE UL-FM R3/4\" K8,1 T68º"},
                {"Codigo": "0133 GP", "Descripcion_Completa": "SPRINKLER PENDIENTE R3/4\" K8,1 T68º"}
            ]
        },
        "INCEN-SANIT": {
            "Descripcion_Base": "Sprinkler de 3/4″",
            "Variantes": [
                {"Codigo": "SPK.UPR.340801", "Descripcion_Completa": "Sprinkler de 3/4\" Up-Right K=8 con fusible ampolla a 68°C sello ULFM-"},
                {"Codigo": "SPK.PEN.340801", "Descripcion_Completa": "Sprinkler de 3/4\" Pendent K=8 con fusible ampolla a 68°C sello UL-FM"}
            ]
        }
    }
}


def normalize_provider_name(provider_name: str) -> str:
    """Normalize provider name for dictionary lookup."""
    normalized = provider_name.upper().strip()
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
    1. First pass: Try exact SKU match in Variantes
    2. Second pass: Try fuzzy matching on Descripcion_Completa of each variant
    """
    normalized_provider = normalize_provider_name(provider_name)
    product_normalized = product_name.lower().strip()

    # FIRST PASS: Try SKU matching (most reliable)
    if sku and sku.strip():
        sku_clean = sku.strip()
        for product_key, product_data in DICCIONARIO_MAESTRO_POR_VARIANTES.items():
            if normalized_provider not in product_data:
                continue

            provider_data = product_data[normalized_provider]
            variantes = provider_data.get("Variantes", [])

            # Check if SKU matches any variant
            for variante in variantes:
                if variante.get("Codigo") == sku_clean:
                    return product_data["Tipo_Estandar"]

    # SECOND PASS: Try fuzzy matching on Descripcion_Completa
    for product_key, product_data in DICCIONARIO_MAESTRO_POR_VARIANTES.items():
        if normalized_provider not in product_data:
            continue

        provider_data = product_data[normalized_provider]
        variantes = provider_data.get("Variantes", [])

        if not variantes:
            continue

        # Try to match against any variant's Descripcion_Completa
        for variante in variantes:
            descripcion = variante.get("Descripcion_Completa", "")
            if descripcion:
                descripcion_normalized = descripcion.lower().strip()
                similarity = fuzz.partial_ratio(product_normalized, descripcion_normalized)

                # If similarity is high enough, consider it a match
                if similarity >= 75:  # Slightly higher threshold for variant matching
                    return product_data["Tipo_Estandar"]

    return None
