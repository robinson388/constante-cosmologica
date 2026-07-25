#!/usr/bin/env python3
"""
Cierre chi via S_vac(P) — formula multiplicativa IR (GRAVEDAD3 + VACIO).

sigma_eff = sigma_stack * (sigma_GH/sigma_stack) * P0 * L_loc * f_lambda
  sigma_GH = k_B T_GH / (4 l_P^2)
  L_loc = sqrt( ln(R_H/l_P) / ln(S_hor) )
  f_lambda = sqrt(1 + 2 lambda_P P0^4 / (rho_crit c^2))
  lambda_P = 4 rho_L c^2 / P0^4   (sector V(P); chi no usa Omega_L)

Chi no contiene Omega_L; comparacion al final solamente.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent / "camino12_chi_Svac_outputs.json"

G = 6.67430e-11
C = 299_792_458.0
HBAR = 1.054571817e-34
K_B = 1.380649e-23
L_PL = math.sqrt(HBAR * G / C**3)
H0 = 67.4 * 1000.0 / 3.085677581e22
R_H = C / H0
A_H = 4.0 * math.pi * R_H**2
RHO_CRIT = 3.0 * H0**2 / (8.0 * math.pi * G)
E_CV = RHO_CRIT * C**2 * (4.0 / 3.0) * math.pi * R_H**3
RHO_L = 0.688 * RHO_CRIT

P0 = 0.1921
PHI0 = 0.10
R_CRIT = (P0 / PHI0) ** 2
OMEGA_M = 0.315
OMEGA_L = 0.688
T_GH = HBAR * H0 / (2.0 * math.pi * K_B)
F_HYST_2D = 0.6718111041787258


def sigma_stack() -> float:
    return RHO_CRIT * C**2 * R_H * P0**2 / R_CRIT


def s_horizon() -> float:
    return A_H / (4.0 * L_PL**2)


def L_loc_IR() -> float:
    return math.sqrt(math.log(R_H / L_PL) / math.log(max(s_horizon(), 2.0)))


def lambda_P_V() -> float:
    """Matching mecanico a escala critica (solo H0, no Omega_L)."""
    return 4.0 * RHO_CRIT * C**2 / P0**4


def lambda_P_from_rho_L() -> float:
    """Alternativa con rho_L (usa Planck)."""
    return 4.0 * RHO_L * C**2 / P0**4


def f_lambda(use_rho_L: bool = False) -> float:
    lam = lambda_P_from_rho_L() if use_rho_L else lambda_P_V()
    return math.sqrt(1.0 + 2.0 * lam * P0**4 / (RHO_CRIT * C**2))


def sigma_GH() -> float:
    return K_B * T_GH / (4.0 * L_PL**2)


def sigma_eff_Svac_multiplicative(use_rho_L: bool = False) -> dict:
    s0 = sigma_stack()
    sg = sigma_GH()
    ll = L_loc_IR()
    fl = f_lambda(use_rho_L=use_rho_L)
    # Acoplamiento chi: fraccion GH localizada por P0 (VACIO) y L_loc (S_hor)
    enh_chi = (sg / s0) * P0 * ll
    enh_total = enh_chi * math.sqrt(fl)
    s_eff = s0 * enh_total
    alpha = s_eff * A_H / E_CV
    x = OMEGA_M / (2.0 * alpha)
    return {
        "sigma_stack": s0,
        "sigma_GH": sg,
        "L_loc": ll,
        "f_lambda": fl,
        "enh_chi": enh_chi,
        "enh_total": enh_total,
        "sigma_eff": s_eff,
        "alpha_s": alpha,
        "x_star": x,
        "delta_vs_Omega_L": x - OMEGA_L,
        "delta_vs_f_hyst_2d": x - F_HYST_2D,
    }


def main() -> None:
    res_crit = sigma_eff_Svac_multiplicative(use_rho_L=False)
    res_planck = sigma_eff_Svac_multiplicative(use_rho_L=True)
    report = {
        "closed_form": (
            "sigma_eff = sigma_stack * (sigma_GH/sigma_stack) * P0 * L_loc * sqrt(f_lambda), "
            "lambda_P = 4 rho_crit c^2 / P0^4 (H0 only)"
        ),
        "inputs": {
            "P0_phi_star": P0,
            "R_crit": R_CRIT,
            "R_H_m": R_H,
            "S_hor": s_horizon(),
            "lambda_P_H0_only": lambda_P_V(),
            "L_loc_formula": "sqrt(ln(R_H/l_P)/ln(S_hor))",
        },
        "result_H0_only": res_crit,
        "result_with_rho_L": res_planck,
        "targets": {"Omega_L": OMEGA_L, "f_hyst_2d": F_HYST_2D},
        "verdict_es": (
            f"H0-only: x*={res_crit['x_star']:.4f} "
            f"(Delta vs Omega_L {res_crit['delta_vs_Omega_L']:+.4f}, "
            f"vs f_hyst {res_crit['delta_vs_f_hyst_2d']:+.4f}). "
            f"Con rho_L: x*={res_planck['x_star']:.4f}."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
