"""Eurocode 7 NBN EN 1997-1 ANB Flemish soil classification library and parameter presets."""

from typing import TypedDict

from settlewell.models import FlemishSoilType, SoilTypeUSCS


class SoilPresetParams(TypedDict):
    """Structure for characteristic Flemish soil preset parameters."""

    name: str
    gamma_dry: float
    gamma_sat: float
    e0: float
    E_modulus: float  # [MPa]
    Cc: float
    Cr: float
    Cv: float  # [m²/yr]
    k_h: float  # [m/s]
    ocr: float
    uscs_type: SoilTypeUSCS
    color: str


FLEMISH_SOIL_PRESETS: dict[FlemishSoilType, SoilPresetParams] = {
    FlemishSoilType.BOOMSE_KLEI: {
        "name": "Boomse Klei (Tertiair)",
        "gamma_dry": 16.0,
        "gamma_sat": 19.0,
        "e0": 0.85,
        "E_modulus": 12.0,
        "Cc": 0.35,
        "Cr": 0.06,
        "Cv": 0.5,
        "k_h": 1e-10,
        "ocr": 3.0,
        "uscs_type": SoilTypeUSCS.CLAY,
        "color": "#451a03",
    },
    FlemishSoilType.IEPERSE_KLEI: {
        "name": "Ieperse / Kortrijkse Klei",
        "gamma_dry": 15.5,
        "gamma_sat": 18.5,
        "e0": 0.95,
        "E_modulus": 10.0,
        "Cc": 0.38,
        "Cr": 0.07,
        "Cv": 0.8,
        "k_h": 5e-10,
        "ocr": 2.5,
        "uscs_type": SoilTypeUSCS.CLAY,
        "color": "#581c87",
    },
    FlemishSoilType.ALLUVIALE_KLEI: {
        "name": "Alluviale Holocene Klei",
        "gamma_dry": 14.0,
        "gamma_sat": 17.0,
        "e0": 1.20,
        "E_modulus": 6.0,
        "Cc": 0.45,
        "Cr": 0.08,
        "Cv": 1.2,
        "k_h": 1e-8,
        "ocr": 1.0,
        "uscs_type": SoilTypeUSCS.CLAY,
        "color": "#854d0e",
    },
    FlemishSoilType.BRABANTSE_LEEM: {
        "name": "Brabantse Leem / Silt",
        "gamma_dry": 16.5,
        "gamma_sat": 19.5,
        "e0": 0.70,
        "E_modulus": 15.0,
        "Cc": 0.18,
        "Cr": 0.03,
        "Cv": 5.0,
        "k_h": 1e-6,
        "ocr": 1.2,
        "uscs_type": SoilTypeUSCS.CLAY,
        "color": "#a16207",
    },
    FlemishSoilType.PLEISTOCEEN_ZAND: {
        "name": "Pleistoceen Fijn/Middel Zand",
        "gamma_dry": 17.5,
        "gamma_sat": 19.5,
        "e0": 0.65,
        "E_modulus": 25.0,
        "Cc": 0.05,
        "Cr": 0.01,
        "Cv": 15.0,
        "k_h": 1e-4,
        "ocr": 1.0,
        "uscs_type": SoilTypeUSCS.SAND,
        "color": "#f59e0b",
    },
    FlemishSoilType.DIESTIAAN_ZAND: {
        "name": "Diestiaan Glauconietzand",
        "gamma_dry": 18.0,
        "gamma_sat": 20.0,
        "e0": 0.60,
        "E_modulus": 35.0,
        "Cc": 0.03,
        "Cr": 0.008,
        "Cv": 25.0,
        "k_h": 2e-4,
        "ocr": 1.5,
        "uscs_type": SoilTypeUSCS.SAND,
        "color": "#d97706",
    },
    FlemishSoilType.BRUSSELIAAN_ZAND: {
        "name": "Brusseliaan Kalkrijk Zand",
        "gamma_dry": 18.5,
        "gamma_sat": 20.5,
        "e0": 0.55,
        "E_modulus": 45.0,
        "Cc": 0.02,
        "Cr": 0.005,
        "Cv": 30.0,
        "k_h": 5e-4,
        "ocr": 1.5,
        "uscs_type": SoilTypeUSCS.SAND,
        "color": "#b45309",
    },
    FlemishSoilType.MAASGRIND: {
        "name": "Maasgrind & Grof Zand",
        "gamma_dry": 19.5,
        "gamma_sat": 21.5,
        "e0": 0.45,
        "E_modulus": 60.0,
        "Cc": 0.01,
        "Cr": 0.002,
        "Cv": 50.0,
        "k_h": 1e-2,
        "ocr": 1.0,
        "uscs_type": SoilTypeUSCS.GRAVEL,
        "color": "#64748b",
    },
    FlemishSoilType.HOLOCEEN_VEEN: {
        "name": "Holoceen Veen / Organisch",
        "gamma_dry": 11.0,
        "gamma_sat": 12.5,
        "e0": 2.50,
        "E_modulus": 2.0,
        "Cc": 1.20,
        "Cr": 0.20,
        "Cv": 0.4,
        "k_h": 1e-5,
        "ocr": 1.0,
        "uscs_type": SoilTypeUSCS.PEAT,
        "color": "#1c1917",
    },
    FlemishSoilType.ANTROPOGEEN: {
        "name": "Antropogene Aanvulling",
        "gamma_dry": 16.0,
        "gamma_sat": 18.0,
        "e0": 0.75,
        "E_modulus": 10.0,
        "Cc": 0.12,
        "Cr": 0.02,
        "Cv": 10.0,
        "k_h": 5e-5,
        "ocr": 1.0,
        "uscs_type": SoilTypeUSCS.SAND,
        "color": "#94a3b8",
    },
}

FLEMISH_PROFILE_TEMPLATES = {
    "Antwerp Boom Clay Formation": [
        ("Aanvulling", FlemishSoilType.ANTROPOGEEN, 1.5),
        ("Pleistoceen Dekzand", FlemishSoilType.PLEISTOCEEN_ZAND, 3.5),
        ("Boomse Klei (Tertiair)", FlemishSoilType.BOOMSE_KLEI, 10.0),
    ],
    "Flemish Coastal Plain Profile": [
        ("Alluviale Deklaag", FlemishSoilType.ALLUVIALE_KLEI, 2.0),
        ("Holoceen Veenlaag", FlemishSoilType.HOLOCEEN_VEEN, 1.5),
        ("Pleistoceen Zand", FlemishSoilType.PLEISTOCEEN_ZAND, 6.0),
    ],
    "Brabant Silt & Sand Profile": [
        ("Brabantse Leem", FlemishSoilType.BRABANTSE_LEEM, 4.0),
        ("Brusseliaan Zand", FlemishSoilType.BRUSSELIAAN_ZAND, 8.0),
    ],
}
