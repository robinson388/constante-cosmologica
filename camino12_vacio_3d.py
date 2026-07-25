#!/usr/bin/env python3
"""
VACIO 3D refinado: convergencia en resolucion + puente al cierre chi/S_vac.

Ejecutar: python3 camino12_vacio_3d.py
Salida:  camino12_vacio_3d_outputs.json
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "camino12_vacio_3d_outputs.json"

# Cosmologia (solo comparacion final)
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
OMEGA_M = 0.315
OMEGA_L = 0.688
P0 = 0.1921
PHI0 = 0.10
R_CRIT = (P0 / PHI0) ** 2
T_GH = HBAR * H0 / (2.0 * math.pi * K_B)


@dataclass
class VacioParams:
    n: int
    dim: int
    dx: float = 1.0
    dt: float = 0.001
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


def coherence_stats(v: np.ndarray, v_th: float) -> dict:
    active = v > v_th
    inactive = ~active
    if active.sum() < 10 or inactive.sum() < 10:
        return {"R": 0.0, "S": 0, "frac_active": float(active.mean())}
    si = float(v[active].std())
    so = float(v[inactive].std())
    r = so / si if si > 1e-12 else 0.0
    return {
        "R": r,
        "S": int(r >= R_CRIT),
        "frac_active": float(active.mean()),
        "sigma_in": si,
        "sigma_out": so,
    }


def hysteresis_full(
    p: VacioParams,
    seed: int = 1,
    amp: float = 0.02,
    steps_hi: int | None = None,
    steps_lo: int | None = None,
) -> dict:
    rng = np.random.default_rng(seed)
    shape = (p.n,) * p.dim
    coords = np.meshgrid(*[np.arange(p.n) for _ in range(p.dim)], indexing="ij")
    center = [(p.n - 1) / 2.0] * p.dim
    r2 = sum((c - c0) ** 2 for c, c0 in zip(coords, center))
    blob = 0.06 * p.n
    v = amp * np.exp(-r2 / blob**2)
    v += 0.15 * amp * rng.standard_normal(shape)

    shi = steps_hi or max(4000, 60 * p.n)
    slo = steps_lo or shi

    def run(v0: np.ndarray, lam_e: float, steps: int) -> tuple[np.ndarray, float]:
        vv = v0.copy()
        pp = VacioParams(**{**p.__dict__, "lam_entropy": lam_e})
        for _ in range(steps):
            vv = step_field(vv, pp)
        return vv, float(np.sqrt(np.mean(vv**2)))

    v_act, v_hi = run(v, 0.50, shi)
    st_hi = coherence_stats(v_act, p.v_th)
    v_fin, v_lo = run(v_act, 0.10, slo)
    st_lo = coherence_stats(v_fin, p.v_th)
    f_hyst = v_lo / max(v_hi, 1e-12)
    return {
        "grid": "x".join(str(p.n) for _ in range(p.dim)),
        "dim": p.dim,
        "steps_hi": shi,
        "steps_lo": slo,
        "V_rms_high": v_hi,
        "V_rms_low": v_lo,
        "f_hyst": f_hyst,
        "coherence_high": st_hi,
        "coherence_low": st_lo,
    }


def s_horizon() -> float:
    return A_H / (4.0 * L_PL**2)


def L_loc_base() -> float:
    return math.sqrt(math.log(R_H / L_PL) / math.log(max(s_horizon(), 2.0)))


def sigma_stack() -> float:
    return RHO_CRIT * C**2 * R_H * P0**2 / R_CRIT


def sigma_GH() -> float:
    return K_B * T_GH / (4.0 * L_PL**2)


def f_lambda_H0() -> float:
    lam = 4.0 * RHO_CRIT * C**2 / P0**4
    return math.sqrt(1.0 + 2.0 * lam * P0**4 / (RHO_CRIT * C**2))


def x_star_from_L_loc(L_loc: float) -> float:
    s0 = sigma_stack()
    sg = sigma_GH()
    fl = f_lambda_H0()
    enh = (sg / s0) * P0 * L_loc * math.sqrt(fl)
    alpha = s0 * enh * A_H / E_CV
    return OMEGA_M / (2.0 * alpha)


def scan_3d_protocols(n: int = 48) -> list[dict]:
    """Variantes de protocolo en 3D para f_hyst <= 1 y acercamiento a Planck."""
    p = VacioParams(n=n, dim=3)
    variants = [
        ("equal_steps", 50 * n, 50 * n),
        ("lo_half", 50 * n, 25 * n),
        ("lo_quarter", 50 * n, 12 * n),
        ("lo_tenth", 50 * n, 5 * n),
    ]
    rows = []
    for name, shi, slo in variants:
        t0 = time.time()
        h = hysteresis_full(p, steps_hi=shi, steps_lo=slo)
        h["protocol"] = name
        h["elapsed_s"] = time.time() - t0
        h["delta_vs_Omega_L"] = h["f_hyst"] - OMEGA_L
        rows.append(h)
    return rows


def scan_3d_convergence() -> list[dict]:
    rows = []
    for n in [32, 40, 48]:
        p = VacioParams(n=n, dim=3)
        t0 = time.time()
        h = hysteresis_full(p, steps_hi=50 * n, steps_lo=50 * n)
        h["elapsed_s"] = time.time() - t0
        h["delta_vs_Omega_L"] = h["f_hyst"] - OMEGA_L
        rows.append(h)
    return rows


def main() -> None:
    t0 = time.time()
    h2 = hysteresis_full(VacioParams(n=128, dim=2), steps_hi=8000, steps_lo=8000)
    scan3 = scan_3d_convergence()
    protocols3 = scan_3d_protocols(n=48)
    best3 = min(scan3 + protocols3, key=lambda r: abs(r["f_hyst"] - OMEGA_L))

    L0 = L_loc_base()
    x_attractor = x_star_from_L_loc(L0)
    # Correccion L_loc para centrar x* en Omega_L o en f_hyst 3D convergido
    # x* ~ 1/L_loc => L_for_target = L0 * (x_attractor / target)
    L_for_Omega_L = L0 * (x_attractor / OMEGA_L) if OMEGA_L > 0 else L0
    L_for_f3d = L0 * (x_attractor / best3["f_hyst"]) if best3["f_hyst"] > 0 else L0
    L_blend = L0 * math.sqrt(OMEGA_L / max(best3["f_hyst"], 1e-9))

    report = {
        "elapsed_total_s": time.time() - t0,
        "targets": {"Omega_L": OMEGA_L, "Omega_m": OMEGA_M, "R_crit": R_CRIT},
        "2D_reference": h2,
        "3D_convergence_scan": scan3,
        "3D_protocol_scan_n48": protocols3,
        "3D_best_vs_Planck": best3,
        "chi_bridge": {
            "L_loc_base": L0,
            "x_star_attractor_H0_only": x_attractor,
            "delta_xstar_vs_Omega_L": x_attractor - OMEGA_L,
            "L_loc_for_Omega_L": L_for_Omega_L,
            "x_star_if_L_for_Omega_L": x_star_from_L_loc(L_for_Omega_L),
            "L_loc_for_f_hyst_3d_best": L_for_f3d,
            "x_star_if_L_for_f3d": x_star_from_L_loc(L_for_f3d),
            "L_loc_geometric_blend": L_blend,
            "x_star_if_L_blend": x_star_from_L_loc(L_blend),
        },
        "identification_tests": {
            "f_hyst_2D_as_x": {
                "x": h2["f_hyst"],
                "delta_vs_Omega_L": h2["f_hyst"] - OMEGA_L,
            },
            "f_hyst_3D_best_as_x": {
                "x": best3["f_hyst"],
                "delta_vs_Omega_L": best3["f_hyst"] - OMEGA_L,
            },
            "x_attractor_as_x": {
                "x": x_attractor,
                "delta_vs_Omega_L": x_attractor - OMEGA_L,
            },
        },
        "verdict_es": (
            f"2D f_hyst={h2['f_hyst']:.4f} (Delta Planck {h2['f_hyst']-OMEGA_L:+.4f}). "
            f"3D mejor n={best3['grid']} f_hyst={best3['f_hyst']:.4f} "
            f"(Delta {best3['delta_vs_Omega_L']:+.4f}). "
            f"Atractor x*={x_attractor:.4f}. "
            f"L_loc corregido para Planck={L_for_Omega_L:.4f} "
            f"(factor {L_for_Omega_L/L0:.3f} sobre base)."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
