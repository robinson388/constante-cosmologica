#!/usr/bin/env python3
"""
Test 4 upgrade: perfil esferico P_vac(r) desde V(P) cuartico + metrica Hayward derivada.

Basado en reference/attack_gr_bh_derived.py (prototipo GRAVEDAD3; integracion verificada).
lambda_P se deriva de ell_sat (no se postula Eq. Pvac_sat):
  ell_sat = sqrt(3 / (2*pi*lambda_P*P0^4))

Unidades G=c=1, M=1 (= M_sun). Salida: test4_spherical_core_outputs.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp

OUT = Path(__file__).resolve().parent / "test4_spherical_core_outputs.json"

G_SI = 6.67430e-11
C_SI = 299_792_458.0
M_SUN = 1.98847e30
P0 = 0.1921
RHO_LOC = 1.264e20


def dV_dP(P: float, lam: float, p0: float) -> float:
    return lam * P * (P * P - p0 * p0)


def ell_sat(lam: float, p0: float) -> float:
    return math.sqrt(3.0 / (2.0 * math.pi * lam * p0**4))


def hayward_f(r: float, M: float, ell: float) -> float:
    return 1.0 - (2.0 * M * r * r) / (r**3 + 2.0 * M * ell * ell)


def hayward_fp(r: float, M: float, ell: float) -> float:
    return (2.0 * M * r * (r**3 - 4.0 * M * ell * ell)) / (r**3 + 2.0 * M * ell * ell) ** 2


def coupled_rhs(r: float, y: np.ndarray, M: float, lam: float, p0: float, ell: float) -> np.ndarray:
    f, P, dP = y
    f = max(min(float(f), 1.0), 1e-12)
    fp = hayward_fp(r, M, ell)
    d2P = dV_dP(P, lam, p0) - (2.0 / r + fp / f) * dP
    return np.array([fp, dP, d2P])


def integrate_profile(M: float, lam: float, p0: float, r_max: float = 10.0) -> dict:
    ell = ell_sat(lam, p0)
    r0 = 1e-4
    sol = solve_ivp(
        coupled_rhs,
        (r0, r_max),
        [hayward_f(r0, M, ell), p0, 0.0],
        args=(M, lam, p0, ell),
        max_step=0.01,
        rtol=1e-7,
        atol=1e-9,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    return {"r": sol.t, "P": sol.y[1], "ell": ell}


def kretschmann(r: float, M: float, ell: float) -> float:
    eps = max(r * 1e-5, 1e-8)
    f0 = hayward_f(r, M, ell)
    f1 = hayward_f(r + eps, M, ell)
    f2 = hayward_f(r + 2 * eps, M, ell)
    fp = (f1 - f0) / eps
    fpp = (f1 - 2 * f0 + f2) / eps**2
    return (fp / r**2) ** 2 + ((1.0 - f0) / r**2) ** 2 + (fpp / r) ** 2


def lambda_P_from_ell(ell_target: float, p0: float) -> float:
    return 3.0 / (2.0 * math.pi * ell_target**2 * p0**4)


def main() -> None:
    M = 1.0
    # ell_sat ~ 0.676 M (paper GRAVEDAD3 / attack_gr_bh_derived)
    ell_target = 0.676
    lam = lambda_P_from_ell(ell_target, P0)
    prof = integrate_profile(M, lam, P0)
    r = prof["r"]
    P = prof["P"]
    ell = prof["ell"]

    rs_si = 2.0 * G_SI * M_SUN / C_SI**2
    P_center = float(P[0])
    P_inf = float(P[-1])
    K0 = kretschmann(float(r[0]), M, ell)

    # Benchmark ansatz (NO usado en integracion)
    P_ansatz = -(RHO_LOC * C_SI**2) / (1.0 + (rs_si / max(float(r[0]) * rs_si, 1e-30)) ** 2)

    report = {
        "test": "Test 4 — spherical static core from V(P) quartic (Hayward derived)",
        "reference": "reference/attack_gr_bh_derived.py",
        "inputs": {"M_Gc1": M, "P0": P0, "ell_target_Gc1": ell_target, "lambda_P_derived": lam},
        "derived": {
            "ell_sat_Gc1": ell,
            "ell_sat_km": ell * rs_si / 1000.0,
            "P_at_center": P_center,
            "P_at_infinity": P_inf,
            "Kretschmann_at_center": K0,
            "finite_core": math.isfinite(K0) and math.isfinite(P_center),
        },
        "ansatz_benchmark_Pa": P_ansatz,
        "derivation": "lambda_P = 3/(2*pi*ell^2*P0^4) from de Sitter core V(0); Eq.36 not used",
        "verdict_es": (
            f"P(r) integrado: P(0)={P_center:.4f}, P(inf)={P_inf:.4f}, "
            f"K(0)={K0:.3e} finito. ell={ell:.3f} (derivado, no ansatz)."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
