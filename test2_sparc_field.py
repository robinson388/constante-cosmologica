#!/usr/bin/env python3
"""
Test 2 upgrade: curvas SPARC desde ecuacion de campo esferica (limite AQUAL).

Limite profundo del gradiente escalar (Appendix app:mond_limit):
  div( mu(g/a0) g ) = 4 pi G rho   (identificacion g = K_g |dP/dr|, mu(x)->x)

No importa g_eff = sqrt(g_N a0) como formula externa; integra la EDP
esferica con mu(x) = x / sqrt(1+x^2) (interpolacion suave Newton<->MOND).

Script: test2_sparc_field.py -> test2_sparc_field_outputs.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

OUT = Path(__file__).resolve().parent / "test2_sparc_field_outputs.json"

G = 6.67430e-11
A0 = 1.20e-10
M_SUN = 1.98847e30
KPC_M = 3.086e19


def mu_mond(x: float) -> float:
    """Interpolacion AQUAL: mu->x (MOND) para x<<1, mu->1 (Newton) para x>>1."""
    return x / math.sqrt(1.0 + x * x)


def rho_exp(r: float, M_tot: float, R_d: float) -> float:
    norm = M_tot / (8.0 * math.pi * R_d**3)
    return norm * math.exp(-r / R_d)


def M_enc(r: float, M_tot: float, R_d: float) -> float:
    x = r / R_d
    return M_tot * (1.0 - math.exp(-x) * (1.0 + x))


def aqual_rhs(r: float, y: np.ndarray, M_tot: float, R_d: float) -> np.ndarray:
    """
    y = [F, g] con F = r^2 mu(g/a0) g,  dF/dr = 4 pi G rho r^2,  dg/dr = ...
    Usamos y = [g, dg/dr] y cerramos con la EDP:
      d/dr(r^2 mu g) = 4 pi G rho r^2
    """
    g, dg = y
    g = max(g, 0.0)
    rho = rho_exp(r, M_tot, R_d)
    F = r * r * mu_mond(g / A0) * g
    dF_dr = 4.0 * math.pi * G * rho * r * r
    # dg/dr desde derivada implicita: F = r^2 mu g
    # dF = 2r mu g dr + r^2 d(mu g)
    # aproximar dg/dr por diferenciacion numerica local de F
    mu = mu_mond(g / A0)
    denom = r * r * mu + r * r * g * (1.0 / A0) * (1.0 / (1.0 + (g / A0) ** 2) ** 1.5)
    dg_dr = (dF_dr - 2.0 * r * mu * g) / max(denom, 1e-30)
    return np.array([dg_dr, 0.0])  # placeholder - use alternate formulation


def integrate_g(M_tot: float, R_d: float, r_max: float) -> tuple[np.ndarray, np.ndarray]:
    """Integracion de dF/dr con F = r^2 mu(g/a0) g, recuperando g(r)."""
    rs = np.geomspace(0.01 * R_d, r_max, 4000)
    g = np.zeros_like(rs)
    F = 0.0
    for i, r in enumerate(rs):
        if i == 0:
            g[i] = G * M_enc(r, M_tot, R_d) / r**2
            F = r * r * mu_mond(g[i] / A0) * g[i]
            continue
        dr = r - rs[i - 1]
        dF = 4.0 * math.pi * G * rho_exp(r, M_tot, R_d) * r * r * dr
        F += dF
        # invertir F = r^2 mu(g/a0) g por biseccion en g
        lo, hi = 0.0, max(G * M_tot / r**2, A0 * 100.0)
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            if rs[i] ** 2 * mu_mond(mid / A0) * mid < F:
                lo = mid
            else:
                hi = mid
        g[i] = 0.5 * (lo + hi)
    return rs, g


def v_curve(r_kpc: np.ndarray, M_tot: float, R_d: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rs, g = integrate_g(M_tot, R_d, r_max=55.0 * KPC_M)
    v_field = []
    v_mond = []
    v_kep = []
    for rk in r_kpc:
        r = rk * KPC_M
        idx = int(np.argmin(np.abs(rs - r)))
        gf = float(g[idx])
        gn = G * M_enc(r, M_tot, R_d) / r**2
        gm = math.sqrt(gn * A0) if gn < A0 else gn
        v_field.append(math.sqrt(gf * r) / 1000.0)
        v_mond.append(math.sqrt(gm * r) / 1000.0)
        v_kep.append(math.sqrt(G * M_enc(r, M_tot, R_d) / r) / 1000.0)
    return np.array(v_field), np.array(v_mond), np.array(v_kep)


def main() -> None:
    M_gal = 1.0e11 * M_SUN
    R_d = 3.0 * KPC_M
    r_kpc = np.linspace(5.0, 50.0, 10)

    v_f, v_m, v_k = v_curve(r_kpc, M_gal, R_d)
    rows = []
    for i, rk in enumerate(r_kpc):
        rows.append(
            {
                "r_kpc": float(rk),
                "v_kepler_kms": float(v_k[i]),
                "v_mond_formula_kms": float(v_m[i]),
                "v_aqual_field_kms": float(v_f[i]),
                "delta_aqual_vs_mond_pct": 100.0 * (v_f[i] - v_m[i]) / v_m[i],
            }
        )

    mean_d = float(np.mean(np.abs([r["delta_aqual_vs_mond_pct"] for r in rows])))
    v50 = float(v_f[-1])

    report = {
        "test": "Test 2 — SPARC from spherical AQUAL (field deep-limit)",
        "equation": "d/dr(r^2 mu(g/a0) g) = 4 pi G rho; g = K_g|dP/dr| in Appendix",
        "inputs": {"M_gal_Msun": 1.0e11, "R_d_kpc": 3.0, "a0": A0},
        "curves_kpc": rows,
        "summary": {
            "v_50kpc_aqual_kms": v50,
            "v_50kpc_mond_kms": float(v_m[-1]),
            "mean_abs_delta_pct": mean_d,
            "suite_band_150_250": 150.0 <= v50 <= 250.0,
        },
        "verdict_es": (
            f"AQUAL integrado: v(50kpc)={v50:.1f} km/s, "
            f"MOND formula {v_m[-1]:.1f}, delta medio {mean_d:.1f}%. "
            f"Suite pass={150 <= v50 <= 250}."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
