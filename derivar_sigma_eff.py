#!/usr/bin/env python3
"""Paso 1 v3: atractor cuadratico (passive cost alpha x^2) + sigma stack."""
from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent / "camino12_sigma_outputs.json"

G = 6.67430e-11
C = 299_792_458.0
HBAR = 1.054571817e-34
K_B = 1.380649e-23
L_PL = math.sqrt(HBAR * G / C**3)
H0 = 67.4 * 1000.0 / 3.085677581e22
R_H = C / H0
V_H = (4.0 / 3.0) * math.pi * R_H**3
A_H = 4.0 * math.pi * R_H**2
RHO_CRIT = 3.0 * H0**2 / (8.0 * math.pi * G)
E_CV = RHO_CRIT * C**2 * V_H

P0 = 0.1921
PHI0 = 0.10
R_CRIT = (P0 / PHI0) ** 2
OMEGA_M = 0.315
OMEGA_R = 9.0e-5
OMEGA_L = 0.688
F_HYST = 0.6573795800626862


def alpha_from_sigma(sigma: float) -> float:
    return sigma * A_H / E_CV


def x_star_quadratic(alpha_s: float, omega_m: float = OMEGA_M) -> float:
    """F = (1-x)Om_m + alpha x^2  =>  x* = Om_m / (2 alpha)."""
    if alpha_s <= 0:
        return float("nan")
    return omega_m / (2.0 * alpha_s)


def sigma_stack() -> float:
    """
    Acoplamiento propuesto (GRAVEDAD3 + VACIO):
    sigma = rho_crit c^2 R_H * P0^2 / R_crit
    """
    return RHO_CRIT * C**2 * R_H * P0**2 / R_CRIT


def sigma_stack_enhanced(f_enh: float = 8.0) -> float:
    """Factor f_enh desde histéresis 3D (calibracion pendiente)."""
    return sigma_stack() * f_enh


def main() -> None:
    s_g = sigma_stack()
    a_g = alpha_from_sigma(s_g)
    x_g = x_star_quadratic(a_g)

    s_req = OMEGA_M * E_CV / (2.0 * F_HYST * A_H)
    a_req = alpha_from_sigma(s_req)
    x_req = x_star_quadratic(a_req)

    s_enh = sigma_stack_enhanced(8.0)
    x_enh = x_star_quadratic(alpha_from_sigma(s_enh))

    report = {
        "model": "F/(rho_crit c^2 V_H) = (1-x)Omega_m + alpha_s x^2",
        "stationarity": "x* = Omega_m / (2 alpha_s)",
        "targets": {"Omega_L": OMEGA_L, "f_hyst": F_HYST, "Omega_m": OMEGA_M},
        "sigma_stack_Pa": s_g,
        "alpha_stack": a_g,
        "x_star_stack": x_g,
        "sigma_required_for_f_hyst_Pa": s_req,
        "x_star_required": x_req,
        "sigma_stack_x8_Pa": s_enh,
        "x_star_stack_x8": x_enh,
        "enhancement_factor_to_match_f_hyst": s_req / s_g,
        "fusion_closure": {
            "f_hyst_plus_Omega_m": F_HYST + OMEGA_M,
            "flatness_gap_to_1": 1.0 - F_HYST - OMEGA_M - OMEGA_R,
            "note": "f_hyst+Om_m ~ 0.972; no cierra planitud sola (falta ~2.8%)",
        },
        "verdict_es": (
            "sigma_stack da x*~0.05 (muy bajo). Para x*=f_hyst hace falta "
            f"sigma ~ {s_req:.3e} Pa (~{s_req/s_g:.1f}x sigma_stack). "
            "El factor ~8 es la brecha a cerrar con VACIO 3D + chi(P)."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
