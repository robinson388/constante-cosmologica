#!/usr/bin/env python3
"""Reproducible boundary vacuum density (paper_lambda.tex)."""
from __future__ import annotations

import json
import math

G = 6.67430e-11  # m^3 kg^-1 s^-2
C = 299_792_458.0  # m/s
A0 = 1.20e-10  # m/s^2 (galactic / suite_falsacion_5tests.py)
H0_KM_S_MPC = 67.4
MPC_M = 3.085677581e22
H0 = H0_KM_S_MPC * 1000.0 / MPC_M  # s^-1
OMEGA_L_PLANCK = 0.688

rho_crit = 3.0 * H0**2 / (8.0 * math.pi * G)
omega_boundary = A0 / (C * H0)
rho_boundary = omega_boundary * rho_crit
rho_boundary_alt = 3.0 * A0 * H0 / (8.0 * math.pi * G * C)
rho_lambda_obs = OMEGA_L_PLANCK * rho_crit

out = {
    "H0_km_s_Mpc": H0_KM_S_MPC,
    "a0_m_s2": A0,
    "rho_crit_kg_m3": rho_crit,
    "Omega_boundary_a0_over_cH0": omega_boundary,
    "rho_boundary_kg_m3": rho_boundary,
    "rho_boundary_alt_kg_m3": rho_boundary_alt,
    "Omega_Lambda_Planck": OMEGA_L_PLANCK,
    "rho_Lambda_obs_kg_m3": rho_lambda_obs,
    "ratio_rho_L_over_rho_boundary": rho_lambda_obs / rho_boundary,
}
print(json.dumps(out, indent=2))
assert abs(rho_boundary - rho_boundary_alt) / rho_boundary < 1e-12
