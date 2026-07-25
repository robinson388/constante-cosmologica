#!/usr/bin/env python3
"""
Pipeline Camino 1+2 — tres pasos en orden:
  1) VACIO 3D vs 2D (f_hyst)
  2) Correccion chi(P) / entropia de horizonte en sigma
  3) Acoplamiento lambda_P (rigidez cuartica en borde)

Salida: camino12_pipeline_outputs.json
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "camino12_pipeline_outputs.json"

# --- Constantes SI / cosmologia ---
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
RHO_L = 0.688 * RHO_CRIT

P0 = 0.1921
PHI0 = 0.10
R_CRIT = (P0 / PHI0) ** 2
OMEGA_M = 0.315
OMEGA_L = 0.688
F_HYST_2D = 0.6573795800626862
T_GH = HBAR * H0 / (2.0 * math.pi * K_B)


@dataclass
class VacioParams:
    n: int
    dim: int
    dx: float = 1.0
    dt: float = 0.001
    steps: int = 2500
    D: float = 1.0
    alpha: float = 0.20
    beta: float = 1.0
    kappa: float = 0.20
    lam_mass: float = 0.05
    lam_area: float = 0.35
    lam_entropy: float = 0.50
    v_th: float = 0.30


def laplacian_nd(f: np.ndarray, dx: float) -> np.ndarray:
    out = -2.0 * f * f.ndim / dx**2
    for ax in range(f.ndim):
        out += (np.roll(f, 1, ax) + np.roll(f, -1, ax)) / dx**2
    return out


def biharmonic_nd(f: np.ndarray, dx: float) -> np.ndarray:
    return laplacian_nd(laplacian_nd(f, dx), dx)


def step_field(v: np.ndarray, p: VacioParams) -> np.ndarray:
    dx = p.dx
    v_mean = float(v.mean())
    f_mass = -p.lam_mass * v_mean
    grad2 = sum(
        ((np.roll(v, -1, ax) - np.roll(v, 1, ax)) / (2 * dx)) ** 2 for ax in range(v.ndim)
    )
    f_area = -p.lam_area * laplacian_nd(grad2, dx)
    f_entropy = p.lam_entropy * np.tanh(v - p.v_th)
    dv = (
        p.D * laplacian_nd(v, dx)
        + p.alpha * v
        - p.beta * v**3
        - p.kappa * biharmonic_nd(v, dx)
        + f_mass
        + f_area
        + f_entropy
    )
    return v + p.dt * dv


def hysteresis_run(p: VacioParams, seed: int = 1, amp: float = 0.02) -> dict:
    rng = np.random.default_rng(seed)
    shape = (p.n,) * p.dim
    coords = np.meshgrid(*[np.arange(p.n) for _ in range(p.dim)], indexing="ij")
    center = [(p.n - 1) / 2.0] * p.dim
    r2 = sum((c - c0) ** 2 for c, c0 in zip(coords, center))
    v = amp * np.exp(-r2 / (0.06 * p.n) ** 2)
    v += 0.15 * amp * rng.standard_normal(shape)

    def integrate_from(v0: np.ndarray, lam_e: float, steps: int) -> tuple[np.ndarray, float]:
        vv = v0.copy()
        pp = VacioParams(**{**p.__dict__, "lam_entropy": lam_e, "steps": steps})
        for _ in range(steps):
            vv = step_field(vv, pp)
        return vv, float(np.sqrt(np.mean(vv**2)))

    vv, v_hi = integrate_from(v, 0.50, p.steps)
    _, v_lo = integrate_from(vv, 0.10, max(p.steps // 2, 500))
    f_hyst = v_lo / max(v_hi, 1e-12)
    return {"V_rms_high": v_hi, "V_rms_low": v_lo, "f_hyst": f_hyst}


def paso1_vacio_2d_3d() -> dict:
    t0 = time.time()
    p2 = VacioParams(n=128, dim=2, steps=8000)
    p3 = VacioParams(n=40, dim=3, steps=3500)
    h2 = hysteresis_run(p2)
    h3 = hysteresis_run(p3)
    return {
        "elapsed_s": time.time() - t0,
        "2D": {"grid": "128x128", **h2},
        "3D": {"grid": "40x40x40", **h3},
        "f_3d_over_2d": h3["f_hyst"] / max(h2["f_hyst"], 1e-12),
        "delta_f_hyst_3d_vs_Omega_L": h3["f_hyst"] - OMEGA_L,
    }


def sigma_stack() -> float:
    return RHO_CRIT * C**2 * R_H * P0**2 / R_CRIT


def paso2_chi_shell() -> dict:
    """
    Entropia de horizonte Bekenstein-Hawking -> tension de cascara:
      sigma_chi = k_B T_GH / (4 l_P^2)
    (presion entropica por unidad de area en celda de Planck).
    """
    s_hor = A_H / (4.0 * L_PL**2)
    chi_inv_vol = K_B * T_GH * s_hor / V_H
    sigma_chi = K_B * T_GH / (4.0 * L_PL**2)
    s0 = sigma_stack()
    f_chi = sigma_chi / s0
    # Correccion adimensional alternativa desde curvatura S_vac(P)
    chi_dimless = chi_inv_vol / (RHO_CRIT * C**2)
    f_chi_alt = math.sqrt(1.0 + P0**2 / max(chi_dimless, 1e-300))
    f_chi_mix = math.sqrt(f_chi * min(f_chi_alt, 1e6))
    return {
        "S_hor": s_hor,
        "T_GH_K": T_GH,
        "chi_inv_J_m3": chi_inv_vol,
        "sigma_chi_Pa": sigma_chi,
        "sigma_stack_Pa": s0,
        "f_chi_sigma_ratio": f_chi,
        "f_chi_alt_sqrt": min(f_chi_alt, 1e6),
        "f_chi_geometric_mix": f_chi_mix,
        "note": "f_chi_mix = sqrt(f_chi * f_chi_alt) acota la correccion entropica.",
    }


def paso3_lambda_P() -> dict:
    """
    lambda_P desde matching rho_L = (lambda_P/4) P0^4 (minimo desplazado).
    sigma_lambda = sqrt(2 * V''(P0) * P0^2 * rho_crit c^2 * l_P^2)
    """
    lam_p = 4.0 * RHO_L * C**2 / P0**4
    v_pp = 2.0 * lam_p * P0**2
    sigma_lam = math.sqrt(max(2.0 * v_pp * P0**2 * RHO_CRIT * C**2 * L_PL**2, 0.0))
    s0 = sigma_stack()
    f_lam = sigma_lam / s0
    f_lam_multi = math.sqrt(1.0 + 2.0 * lam_p * P0**4 / (RHO_CRIT * C**2))
    return {
        "lambda_P_match": lam_p,
        "V_pp_at_P0": v_pp,
        "sigma_lambda_Pa": sigma_lam,
        "f_lambda_sigma_ratio": f_lam,
        "f_lambda_multiplicative": f_lam_multi,
        "rho_Lambda_kg_m3": RHO_L,
    }


def alpha_from_sigma(s: float) -> float:
    return s * A_H / E_CV


def x_star(alpha_s: float) -> float:
    return OMEGA_M / (2.0 * alpha_s) if alpha_s > 0 else float("nan")


def paso4_combinar(
    f_hyst_2d: float,
    f_hyst_3d: float,
    f_chi: float,
    f_chi_mix: float,
    f_lam: float,
) -> dict:
    s0 = sigma_stack()
    f3_ratio = f_hyst_3d / max(f_hyst_2d, 1e-12)
    scenarios = {
        "stack_only": 1.0,
        "sqrt_chi_x_lam": math.sqrt(f_chi) * math.sqrt(f_lam),
        "sqrt_chi_mix_x_lam": math.sqrt(f_chi_mix) * math.sqrt(f_lam),
        "f3d_ratio_x_sqrt_chi_lam": f3_ratio * math.sqrt(f_chi) * math.sqrt(f_lam),
        "f_hyst_2d_as_x_target": f_hyst_2d,
        "f_hyst_3d_as_x_target": f_hyst_3d,
    }
    rows = []
    for name, enh in scenarios.items():
        if name.startswith("f_hyst"):
            x = enh
            rows.append(
                {
                    "scenario": name,
                    "x_star": x,
                    "delta_vs_Omega_L": x - OMEGA_L,
                    "sigma_implied_enhancement": (OMEGA_M / (2.0 * x)) / alpha_from_sigma(s0)
                    if x > 0
                    else None,
                }
            )
            continue
        s = s0 * enh
        a = alpha_from_sigma(s)
        x = x_star(a)
        rows.append(
            {
                "scenario": name,
                "enhancement": enh,
                "sigma_Pa": s,
                "alpha_s": a,
                "x_star": x,
                "delta_vs_Omega_L": x - OMEGA_L if math.isfinite(x) else None,
            }
        )
    best = min(
        [r for r in rows if "x_star" in r and math.isfinite(r["x_star"]) and 0 < r["x_star"] <= 1.5],
        key=lambda r: abs(r["x_star"] - OMEGA_L),
        default=None,
    )
    s_req = OMEGA_M * E_CV / (2.0 * OMEGA_L * A_H)
    return {
        "sigma_stack_Pa": s0,
        "sigma_required_Pa": s_req,
        "enhancement_required": s_req / s0,
        "f_hyst_2d_sim": f_hyst_2d,
        "f_hyst_3d_sim": f_hyst_3d,
        "scenarios": rows,
        "best_scenario": best,
    }


def main() -> None:
    print("Paso 1: VACIO 2D vs 3D...")
    p1 = paso1_vacio_2d_3d()
    print("Paso 2: chi(P) shell...")
    p2 = paso2_chi_shell()
    print("Paso 3: lambda_P...")
    p3 = paso3_lambda_P()
    fchi = p2["f_chi_sigma_ratio"]
    fchi_mix = p2["f_chi_geometric_mix"]
    flam = p3["f_lambda_multiplicative"]
    print("Paso 4: combinar...")
    p4 = paso4_combinar(
        p1["2D"]["f_hyst"],
        p1["3D"]["f_hyst"],
        fchi,
        fchi_mix,
        flam,
    )

    report = {
        "paso1_vacio_3d": p1,
        "paso2_chi_shell": p2,
        "paso3_lambda_P": p3,
        "paso4_combined": p4,
        "targets": {"Omega_L": OMEGA_L, "f_hyst_2d": F_HYST_2D, "Omega_m": OMEGA_M},
        "verdict_es": _verdict(p1, p2, p3, p4),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


def _verdict(p1, p2, p3, p4) -> str:
    best = p4.get("best_scenario")
    if best and abs(best["delta_vs_Omega_L"]) < 0.05:
        return (
            f"Cierre parcial: escenario '{best['scenario']}' da "
            f"x*={best['x_star']:.3f} (objetivo {OMEGA_L})."
        )
    return (
        f"Brecha restante: enhancement requerido ~{p4['enhancement_required']:.1f}x. "
        f"f_hyst 2D={p1['2D']['f_hyst']:.3f}, 3D={p1['3D']['f_hyst']:.3f}, "
        f"chi={p2['f_chi_sigma_ratio']:.1f}x, lambda={p3['f_lambda_multiplicative']:.2f}x."
    )


if __name__ == "__main__":
    main()
