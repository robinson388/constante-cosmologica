#!/usr/bin/env python3
"""
Correccion O((P-P0)^3) a S_vac(P) — cierre del residual ~2.5% en x* (H0-only).

S_vac(P) = S_0 - (chi/2)(P-P0)^2 + (zeta/6)(P-P0)^3

Shell IR (VACIO @ R_crit): Delta_P = P0/sqrt(R_crit) = phi_0
Asimetria de activacion: eta = (P0 - phi_0) / P0

Matching GRAVEDAD3–VACIO (sin Omega_L):
  zeta/chi = eta / (3 Delta_P) = eta / (3 phi_0)

Correccion al factor de localizacion IR (expansion a primer orden):
  L_loc -> L_loc * (1 - eta/18)

Entonces x* sube ~ (1 - eta/18)^(-1) desde la base cuadratica.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent / "camino12_Svac_cubic_outputs.json"

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

P0 = 0.1921
PHI0 = 0.10
R_CRIT = (P0 / PHI0) ** 2
OMEGA_M = 0.315
OMEGA_L = 0.688
T_GH = HBAR * H0 / (2.0 * math.pi * K_B)
F_HYST_2D = 0.6718111041787258


def s_horizon() -> float:
    return A_H / (4.0 * L_PL**2)


def L_loc_quadratic() -> float:
    return math.sqrt(math.log(R_H / L_PL) / math.log(max(s_horizon(), 2.0)))


def eta_asymmetry() -> float:
    return (P0 - PHI0) / P0


def delta_P_shell() -> float:
    """Excursion IR en R_crit (VACIO): P0/sqrt(R_crit) = phi_0."""
    return P0 / math.sqrt(R_CRIT)


def zeta_over_chi(eta: float, delta_p: float) -> float:
    """zeta/chi fijado por asimetria VACIO en la corteza de horizonte."""
    return eta / (3.0 * delta_p)


def L_loc_cubic_factor(eta: float) -> float:
    """L_eff = L_quad * (1 - eta/18); signo: cubic reduce L, sube x*."""
    return 1.0 - eta / 18.0


def sigma_stack() -> float:
    return RHO_CRIT * C**2 * R_H * P0**2 / R_CRIT


def sigma_GH() -> float:
    return K_B * T_GH / (4.0 * L_PL**2)


def f_lambda_H0() -> float:
    lam = 4.0 * RHO_CRIT * C**2 / P0**4
    return math.sqrt(1.0 + 2.0 * lam * P0**4 / (RHO_CRIT * C**2))


def x_star_from_L(L_loc: float) -> float:
    s0 = sigma_stack()
    sg = sigma_GH()
    fl = f_lambda_H0()
    enh = (sg / s0) * P0 * L_loc * math.sqrt(fl)
    alpha = s0 * enh * A_H / E_CV
    return OMEGA_M / (2.0 * alpha)


def chi_mechanical() -> float:
    """Curvatura entropica dual a V''(P0)=2 lambda_P P0^2 (GRAVEDAD3)."""
    lam = 4.0 * RHO_CRIT * C**2 / P0**4
    return 2.0 * lam * P0**2 / T_GH


def zeta_absolute(z_over_c: float) -> float:
    return z_over_c * chi_mechanical()


def x_star_with_zeta_factor(zeta_factor: float = 1.0) -> float:
    """Varia zeta/chi nominal por zeta_factor."""
    f_cubic = 1.0 - zeta_factor * eta_asymmetry() / 18.0
    return x_star_from_L(L_loc_quadratic() * f_cubic)


def quartic_to_cubic_ratio() -> float:
    """|xi| Delta / (4|zeta|) con xi ~ V''''/T_GH, zeta ~ V'''/T_GH."""
    lam = 4.0 * RHO_CRIT * C**2 / P0**4
    v4pp = 6.0 * lam  # V'''' for quartic V
    v3p = 6.0 * lam * P0  # V'''(P0)
    eta = eta_asymmetry()
    delta_p = delta_P_shell()
    zeta = (eta / (3.0 * delta_p)) * chi_mechanical()
    xi = v4pp / T_GH
    return abs(xi) * delta_p / (4.0 * abs(zeta))


def overfitting_audit() -> list[dict]:
    rows = []
    for label, fac in [("0.80x", 0.8), ("nominal", 1.0), ("1.20x", 1.2)]:
        x = x_star_with_zeta_factor(fac)
        rows.append(
            {
                "zeta_factor": fac,
                "label": label,
                "x_star": x,
                "delta_vs_Omega_L": x - OMEGA_L,
                "pct_vs_Omega_L": 100.0 * (x - OMEGA_L) / OMEGA_L,
            }
        )
    return rows


def main() -> None:
    eta = eta_asymmetry()
    delta_p = delta_P_shell()
    zoc = zeta_over_chi(eta, delta_p)
    f_cubic = L_loc_cubic_factor(eta)
    L_quad = L_loc_quadratic()
    L_cubic = L_quad * f_cubic

    x_quad = x_star_from_L(L_quad)
    x_cubic = x_star_from_L(L_cubic)
    audit = overfitting_audit()

    report = {
        "model": (
            "S_vac = S0 - (chi/2)(P-P0)^2 + (zeta/6)(P-P0)^3; "
            "L_loc -> L_quad * (1 - eta/18), eta=(P0-phi0)/P0"
        ),
        "inputs": {
            "P0": P0,
            "phi_0": PHI0,
            "R_crit": R_CRIT,
            "eta": eta,
            "Delta_P_shell": delta_p,
            "zeta_over_chi": zoc,
            "chi_mechanical_J_per_K_m3": chi_mechanical(),
            "zeta_J_per_K_m4": zeta_absolute(zoc),
        },
        "L_loc": {
            "quadratic": L_quad,
            "cubic_factor": f_cubic,
            "cubic_corrected": L_cubic,
            "audit_wrong_factor_Omega_over_x": OMEGA_L / x_quad,
            "correct_factor_x_over_Omega": x_quad / OMEGA_L,
        },
        "x_star": {
            "quadratic_H0_only": x_quad,
            "cubic_corrected_H0_only": x_cubic,
            "delta_vs_Omega_L_quad": x_quad - OMEGA_L,
            "delta_vs_Omega_L_cubic": x_cubic - OMEGA_L,
            "delta_vs_f_hyst_2d_cubic": x_cubic - F_HYST_2D,
            "pct_vs_Omega_L_cubic": 100.0 * (x_cubic - OMEGA_L) / OMEGA_L,
        },
        "targets": {"Omega_L": OMEGA_L, "f_hyst_2d": F_HYST_2D},
        "quartic_truncation": {
            "ratio_xiDelta_over_4zeta": quartic_to_cubic_ratio(),
            "interpretation": "~0.1 => O(10%) quartic on shell; not permille-exact",
        },
        "overfitting_audit": audit,
        "verdict_es": (
            f"Cuadratico x*={x_quad:.4f} (Delta Omega_L {x_quad - OMEGA_L:+.4f}). "
            f"Cubico eta/18={eta/18:.4f}, L_factor={f_cubic:.4f}, "
            f"x*={x_cubic:.4f} (Delta Omega_L {x_cubic - OMEGA_L:+.4f}, "
            f"{100.0 * (x_cubic - OMEGA_L) / OMEGA_L:+.2f}%). "
            "Sin input Omega_L en zeta/chi."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
