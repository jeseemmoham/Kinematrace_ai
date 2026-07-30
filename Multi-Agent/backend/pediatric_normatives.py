"""
pediatric_normatives.py

Centralized configuration for pediatric gait screening reference profiles and risk thresholds.
Designed for toddlers and young children aged 1-4 years.
Note: These values are conservative screening reference ranges for automated
motion tracking, not formal clinical diagnostic criteria.
"""

from typing import Dict, Any

PEDIATRIC_NORMATIVE_PROFILES: Dict[str, Dict[str, Any]] = {
    "1-2": {
        "age_group": "1-2 years (Toddler Early Walkers)",
        "knee_rom_deg": {"min": 30.0, "max": 75.0, "target": 52.0},
        "hip_rom_deg": {"min": 25.0, "max": 60.0, "target": 45.0},
        "gait_symmetry_min_pct": 88.0,
        "mean_asymmetry_max_pct": 12.0,
        "peak_asymmetry_max_pct": 25.0,
        "rom_difference_max_deg": 12.0,
    },
    "2-3": {
        "age_group": "2-3 years (Toddler Maturing Walkers)",
        "knee_rom_deg": {"min": 35.0, "max": 80.0, "target": 58.0},
        "hip_rom_deg": {"min": 30.0, "max": 65.0, "target": 48.0},
        "gait_symmetry_min_pct": 90.0,
        "mean_asymmetry_max_pct": 10.0,
        "peak_asymmetry_max_pct": 20.0,
        "rom_difference_max_deg": 10.0,
    },
    "3-4": {
        "age_group": "3-4 years (Young Children Established Gait)",
        "knee_rom_deg": {"min": 40.0, "max": 85.0, "target": 62.0},
        "hip_rom_deg": {"min": 30.0, "max": 70.0, "target": 50.0},
        "gait_symmetry_min_pct": 90.0,
        "mean_asymmetry_max_pct": 10.0,
        "peak_asymmetry_max_pct": 20.0,
        "rom_difference_max_deg": 10.0,
    },
    "default": {
        "age_group": "Pediatric Toddler Baseline (1-4 years)",
        "knee_rom_deg": {"min": 30.0, "max": 80.0, "target": 55.0},
        "hip_rom_deg": {"min": 25.0, "max": 65.0, "target": 48.0},
        "gait_symmetry_min_pct": 90.0,
        "mean_asymmetry_max_pct": 10.0,
        "peak_asymmetry_max_pct": 20.0,
        "rom_difference_max_deg": 10.0,
    }
}

PEDIATRIC_RISK_CONFIG: Dict[str, Any] = {
    "age_group": "1-4 years (Toddlers & Young Children)",
    "gait_symmetry": {
        "normal_min": 90.0,
        "moderate_threshold": 90.0,
        "high_threshold": 85.0
    },
    "mean_symmetry_index": {
        "normal_max": 10.0,
        "moderate_threshold": 10.0,
        "high_threshold": 15.0
    },
    "peak_symmetry_index": {
        "normal_max": 20.0,
        "high_threshold": 25.0
    },
    "rom_difference": {
        "normal_max": 10.0,
        "moderate_threshold": 10.0,
        "high_threshold": 15.0
    },
    "knee_rom": {
        "normal_min": 30.0,
        "normal_max": 80.0
    },
    "hip_rom": {
        "normal_min": 25.0,
        "normal_max": 65.0
    }
}


def get_pediatric_normative_profile(age_str: str = None) -> Dict[str, Any]:
    """
    Selects appropriate pediatric normative profile based on patient age.
    """
    if not age_str:
        return PEDIATRIC_NORMATIVE_PROFILES["default"]

    age_str_lower = str(age_str).lower().strip()

    if "1" in age_str_lower and ("2" in age_str_lower or "18m" in age_str_lower or "1 y" in age_str_lower):
        return PEDIATRIC_NORMATIVE_PROFILES["1-2"]
    elif "2" in age_str_lower and ("3" in age_str_lower or "2 y" in age_str_lower):
        return PEDIATRIC_NORMATIVE_PROFILES["2-3"]
    elif ("3" in age_str_lower or "4" in age_str_lower) and ("4" in age_str_lower or "3 y" in age_str_lower):
        return PEDIATRIC_NORMATIVE_PROFILES["3-4"]

    return PEDIATRIC_NORMATIVE_PROFILES["default"]
