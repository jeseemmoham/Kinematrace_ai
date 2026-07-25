"""
clinical_math.py

Modular Python module for clinical kinematic calculations and gait risk analysis
using NumPy and Pandas.
"""

from typing import Dict, Union, Tuple
import numpy as np
import pandas as pd


def _calculate_angle_vectorized(
    h_coords: np.ndarray,
    k_coords: np.ndarray,
    a_coords: np.ndarray
) -> np.ndarray:
    """
    Helper function to compute interior joint angle at vertex K in 3D space.

    Args:
        h_coords (np.ndarray): (N, 3) coordinates for Hip.
        k_coords (np.ndarray): (N, 3) coordinates for Knee.
        a_coords (np.ndarray): (N, 3) coordinates for Ankle.

    Returns:
        np.ndarray: Array of shape (N,) containing angles in degrees [0, 180].
    """
    v_hk = h_coords - k_coords  # Vector from Knee to Hip
    v_ka = a_coords - k_coords  # Vector from Knee to Ankle

    dot_product = np.sum(v_hk * v_ka, axis=1)
    norm_hk = np.linalg.norm(v_hk, axis=1)
    norm_ka = np.linalg.norm(v_ka, axis=1)

    denom = norm_hk * norm_ka
    # Suppress division by zero or NaN warnings
    with np.errstate(divide='ignore', invalid='ignore'):
        cos_angle = np.where(denom > 1e-8, dot_product / denom, np.nan)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angles_rad = np.arccos(cos_angle)
        angles_deg = np.degrees(angles_rad)

    return angles_deg


def calculate_joint_angles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the 3D interior flexion angle of the left knee and right knee for every frame.

    Args:
        df (pd.DataFrame): DataFrame containing 3D joint coordinates extracted by cv_engine.py.

    Returns:
        pd.DataFrame: DataFrame indexed by frame with 'left_knee_angle' and 'right_knee_angle' columns.
    """
    left_hip = df[["left_hip_x", "left_hip_y", "left_hip_z"]].values
    left_knee = df[["left_knee_x", "left_knee_y", "left_knee_z"]].values
    left_ankle = df[["left_ankle_x", "left_ankle_y", "left_ankle_z"]].values

    right_hip = df[["right_hip_x", "right_hip_y", "right_hip_z"]].values
    right_knee = df[["right_knee_x", "right_knee_y", "right_knee_z"]].values
    right_ankle = df[["right_ankle_x", "right_ankle_y", "right_ankle_z"]].values

    left_angles = _calculate_angle_vectorized(left_hip, left_knee, left_ankle)
    right_angles = _calculate_angle_vectorized(right_hip, right_knee, right_ankle)

    angles_df = pd.DataFrame(
        {
            "left_knee_angle": left_angles,
            "right_knee_angle": right_angles,
        },
        index=df.index
    )

    return angles_df


def compute_symmetry_index(
    left_angles: Union[pd.Series, np.ndarray],
    right_angles: Union[pd.Series, np.ndarray]
) -> Union[pd.Series, np.ndarray]:
    """
    Computes the bilateral Symmetry Index (SI) across the time series using the clinical formula:
    SI = |left - right| / ((left + right) / 2) * 100

    Args:
        left_angles (pd.Series or np.ndarray): Time series of left joint angles.
        right_angles (pd.Series or np.ndarray): Time series of right joint angles.

    Returns:
        pd.Series or np.ndarray: Calculated Symmetry Index values per frame.
    """
    is_series = isinstance(left_angles, pd.Series)
    l_arr = left_angles.values if is_series else np.asarray(left_angles)
    r_arr = right_angles.values if is_series else np.asarray(right_angles)

    denom = (l_arr + r_arr) / 2.0
    with np.errstate(divide='ignore', invalid='ignore'):
        si = np.where(
            (denom != 0) & ~np.isnan(denom),
            (np.abs(l_arr - r_arr) / denom) * 100.0,
            np.nan
        )

    if is_series:
        return pd.Series(si, index=left_angles.index, name="symmetry_index")
    return si


def evaluate_gait_risk(df: pd.DataFrame) -> Dict[str, Union[str, float]]:
    """
    Evaluates gait risk based on mean bilateral Symmetry Index across time frames.

    If mean SI > 15%, returns HIGH ASYMMETRY DETECTED (red).
    Otherwise, returns NORMATIVE GAIT (green).

    Args:
        df (pd.DataFrame): Input DataFrame containing joint coordinates or pre-calculated angles.

    Returns:
        dict: {"status": str, "risk_score": float, "color": str}
    """
    if "left_knee_angle" not in df.columns or "right_knee_angle" not in df.columns:
        angles_df = calculate_joint_angles(df)
        left_angles = angles_df["left_knee_angle"]
        right_angles = angles_df["right_knee_angle"]
    else:
        left_angles = df["left_knee_angle"]
        right_angles = df["right_knee_angle"]

    si_series = compute_symmetry_index(left_angles, right_angles)
    mean_si = float(np.nanmean(si_series)) if not np.all(np.isnan(si_series)) else 0.0

    if mean_si > 15.0:
        return {
            "status": "HIGH ASYMMETRY DETECTED",
            "risk_score": round(mean_si, 2),
            "color": "red"
        }
    else:
        return {
            "status": "NORMATIVE GAIT",
            "risk_score": round(mean_si, 2),
            "color": "green"
        }


if __name__ == "__main__":
    print("clinical_math.py loaded successfully.")
