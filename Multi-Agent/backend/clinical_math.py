"""
backend/clinical_math.py

Modular Python module for clinical kinematic calculations and gait risk analysis
using NumPy and Pandas.
Supports pediatric gait screening for toddlers and young children aged 1-4 years.
"""

from typing import Dict, Union, Tuple, Any
import numpy as np
import pandas as pd


def _calculate_angle_vectorized(
    h_coords: np.ndarray,
    k_coords: np.ndarray,
    a_coords: np.ndarray
) -> np.ndarray:
    """
    Helper function to compute interior joint angle at vertex K in 3D space.

    v1 = H - K
    v2 = A - K
    cos_theta = dot(v1, v2) / (norm(v1) * norm(v2))
    theta = arccos(clip(cos_theta, -1.0, 1.0)) * 180 / pi
    """
    v_hk = h_coords - k_coords  # Vector from Knee to Hip
    v_ka = a_coords - k_coords  # Vector from Knee to Ankle

    dot_product = np.sum(v_hk * v_ka, axis=1)
    norm_hk = np.linalg.norm(v_hk, axis=1)
    norm_ka = np.linalg.norm(v_ka, axis=1)

    denom = norm_hk * norm_ka
    with np.errstate(divide='ignore', invalid='ignore'):
        cos_angle = np.where(denom > 1e-6, dot_product / denom, np.nan)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angles_rad = np.arccos(cos_angle)
        angles_deg = np.degrees(angles_rad)

    return angles_deg


def calculate_joint_angles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the 3D interior flexion angle of the left knee, right knee, and hips for every frame.
    Strict MediaPipe Landmark Mapping:
    - Left: LEFT_HIP (23) -> LEFT_KNEE (25) -> LEFT_ANKLE (27)
    - Right: RIGHT_HIP (24) -> RIGHT_KNEE (26) -> RIGHT_ANKLE (28)
    """
    left_hip = df[["left_hip_x", "left_hip_y", "left_hip_z"]].values
    left_knee = df[["left_knee_x", "left_knee_y", "left_knee_z"]].values
    left_ankle = df[["left_ankle_x", "left_ankle_y", "left_ankle_z"]].values

    right_hip = df[["right_hip_x", "right_hip_y", "right_hip_z"]].values
    right_knee = df[["right_knee_x", "right_knee_y", "right_knee_z"]].values
    right_ankle = df[["right_ankle_x", "right_ankle_y", "right_ankle_z"]].values

    left_knee_angles = _calculate_angle_vectorized(left_hip, left_knee, left_ankle)
    right_knee_angles = _calculate_angle_vectorized(right_hip, right_knee, right_ankle)

    result_dict = {
        "left_knee_angle": left_knee_angles,
        "right_knee_angle": right_knee_angles,
    }

    if "left_shoulder_x" in df.columns and "left_shoulder_y" in df.columns and "left_shoulder_z" in df.columns:
        left_sh = df[["left_shoulder_x", "left_shoulder_y", "left_shoulder_z"]].values
        right_sh = df[["right_shoulder_x", "right_shoulder_y", "right_shoulder_z"]].values
        left_hip_angles = _calculate_angle_vectorized(left_sh, left_hip, left_knee)
        right_hip_angles = _calculate_angle_vectorized(right_sh, right_hip, right_knee)
        result_dict["left_hip_angle"] = left_hip_angles
        result_dict["right_hip_angle"] = right_hip_angles

    angles_df = pd.DataFrame(result_dict, index=df.index)
    return angles_df


def compute_symmetry_index(
    left_angles: Union[pd.Series, np.ndarray],
    right_angles: Union[pd.Series, np.ndarray]
) -> Union[pd.Series, np.ndarray]:
    """
    Computes bilateral Symmetry Index (SI) across movement sequence.

    Formula:
    SI = 100 * |Left - Right| / (0.5 * (|Left| + |Right|))
    Gait Symmetry = max(0, 100 - SI)

    Note: Cross-leg phase differences are accounted for by evaluating cycle-level parameters
    (such as peak Range of Motion) rather than raw unsynchronized frame t angles.
    """
    is_series = isinstance(left_angles, pd.Series)
    l_arr = left_angles.values if is_series else np.asarray(left_angles, dtype=float)
    r_arr = right_angles.values if is_series else np.asarray(right_angles, dtype=float)

    denom = 0.5 * (np.abs(l_arr) + np.abs(r_arr))
    with np.errstate(divide='ignore', invalid='ignore'):
        si_array = np.where(denom > 1e-6, (np.abs(l_arr - r_arr) / denom) * 100.0, 0.0)

    if is_series:
        return pd.Series(si_array, index=left_angles.index, name="symmetry_index")
    return si_array


def evaluate_gait_risk(df: pd.DataFrame) -> Dict[str, Union[str, float]]:
    """
    Evaluates gait risk based on bilateral Symmetry Index and ROM deficit.
    """
    if "left_knee_angle" not in df.columns or "right_knee_angle" not in df.columns:
        angles_df = calculate_joint_angles(df)
    else:
        angles_df = df

    left_angles = angles_df["left_knee_angle"].dropna()
    right_angles = angles_df["right_knee_angle"].dropna()

    if not left_angles.empty and len(left_angles) > 5:
        l_max = float(np.percentile(left_angles, 95))
        l_min = float(np.percentile(left_angles, 5))
    else:
        l_max = float(left_angles.max()) if not left_angles.empty else 110.0
        l_min = float(left_angles.min()) if not left_angles.empty else 10.0

    if not right_angles.empty and len(right_angles) > 5:
        r_max = float(np.percentile(right_angles, 95))
        r_min = float(np.percentile(right_angles, 5))
    else:
        r_max = float(right_angles.max()) if not right_angles.empty else 110.0
        r_min = float(right_angles.min()) if not right_angles.empty else 10.0

    l_rom = max(0.0, l_max - l_min)
    r_rom = max(0.0, r_max - r_min)

    # Compute parameter-based ROM Symmetry Index
    rom_denom = 0.5 * (abs(l_rom) + abs(r_rom))
    if rom_denom > 1e-6:
        mean_si = (abs(l_rom - r_rom) / rom_denom) * 100.0
    else:
        mean_si = 0.0

    rom_deficit_deg = abs(l_rom - r_rom)

    if mean_si < 10.0 and rom_deficit_deg < 10.0:
        status = "NORMAL"
        risk_score = 0.0
        color = "GREEN"
    elif mean_si < 15.0 and rom_deficit_deg < 15.0:
        status = "MILD_ASYMMETRY"
        risk_score = 1.0
        color = "YELLOW"
    else:
        status = "HIGH_ASYMMETRY"
        risk_score = 2.0
        color = "RED"

    return {
        "status": status,
        "risk_score": risk_score,
        "color": color,
        "mean_si": round(mean_si, 1),
        "l_rom": round(l_rom, 1),
        "r_rom": round(r_rom, 1),
        "rom_deficit_deg": round(rom_deficit_deg, 1),
    }
