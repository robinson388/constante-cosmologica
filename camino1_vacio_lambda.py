#!/usr/bin/env python3
"""
Camino 1: ¿Puede VACIO (nucleacion + histéresis) predecir Omega_Lambda ~ 0.69
SIN meter Planck/CMB como input?

Ejecutar: python3 camino1_vacio_lambda.py
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent / "camino1_outputs.json"

# --- Observables cosmologicos (solo para COMPARAR al final, no entran al modelo VACIO)
G = 6.67430e-11
C = 299_792_458.0
H0_KM_S_MPC = 67.4
MPC_M = 3.085677581e22
H0 = H0_KM_S_MPC * 1000.0 / MPC_M
OMEGA_L_TARGET = 0.688
RHO_CRIT = 3.0 * H0**2 / (8.0 * math.pi * G)


@dataclass
class VacioParams:
    n: int = 128
    dx: float = 1.0
    dt: float = 0.001
    steps: int = 15000
    D: float = 1.0
    alpha: float = 0.20
    beta: float = 1.0
    kappa: float = 0.20
    lam_mass: float = 0.05
    lam_area: float = 0.35
    lam_entropy: float = 0.50
    v_th: float = 0.30
    phi_star: float = 0.1921
    phi_0: float = 0.10


def laplacian(f: np.ndarray, dx: float) -> np.ndarray:
    return (
        np.roll(f, 1, 0)
        + np.roll(f, -1, 0)
        + np.roll(f, 1, 1)
        + np.roll(f, -1, 1)
        - 4.0 * f
    ) / dx**2


def biharmonic(f: np.ndarray, dx: float) -> np.ndarray:
    return laplacian(laplacian(f, dx), dx)


def coherence_stats(v: np.ndarray, v_th: float) -> dict:
    active = v > v_th
    inactive = ~active
    frac_active = float(active.mean())
    if active.sum() < 10 or inactive.sum() < 10:
        return {
            "R": 0.0,
            "S": 0,
            "frac_active": frac_active,
            "sigma_in": 0.0,
            "sigma_out": 0.0,
        }
    sigma_in = float(v[active].std())
    sigma_out = float(v[inactive].std())
    if sigma_in < 1e-12:
        r = float("inf") if sigma_out > 0 else 0.0
    else:
        r = sigma_out / sigma_in
    r_crit = (0.1921 / 0.10) ** 2
    return {
        "R": float(r if math.isfinite(r) else 999.0),
        "S": int(r >= r_crit),
        "frac_active": frac_active,
        "sigma_in": sigma_in,
        "sigma_out": sigma_out,
        "R_crit": r_crit,
    }


def step_vacio(v: np.ndarray, p: VacioParams) -> np.ndarray:
    dx = p.dx
    v_mean = float(v.mean())
    # Restriccion global suave (conservacion aproximada de masa total)
    f_mass = -p.lam_mass * v_mean
    grad_x = (np.roll(v, -1, 1) - np.roll(v, 1, 1)) / (2 * dx)
    grad_y = (np.roll(v, -1, 0) - np.roll(v, 1, 0)) / (2 * dx)
    grad2 = grad_x**2 + grad_y**2
    f_area = -p.lam_area * laplacian(grad2, dx)
    f_entropy = p.lam_entropy * np.tanh(v - p.v_th)
    dv = (
        p.D * laplacian(v, dx)
        + p.alpha * v
        - p.beta * v**3
        - p.kappa * biharmonic(v, dx)
        + f_mass
        + f_area
        + f_entropy
    )
    return v + p.dt * dv


def run_vacio(
    amplitude: float,
    p: VacioParams,
    seed: int = 0,
    lam_entropy: float | None = None,
) -> dict:
    rng = np.random.default_rng(seed)
    p = VacioParams(**{**p.__dict__})
    if lam_entropy is not None:
        p.lam_entropy = lam_entropy
    x = np.arange(p.n)
    y = np.arange(p.n)
    X, Y = np.meshgrid(x, y, indexing="ij")
    cx, cy = p.n // 2, p.n // 2
    v = amplitude * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (0.08 * p.n) ** 2)
    v += 0.1 * amplitude * rng.standard_normal((p.n, p.n))
    for _ in range(p.steps):
        v = step_vacio(v, p)
    st = coherence_stats(v, p.v_th)
    v_sat = math.sqrt(p.alpha / p.beta)
    e_density = float(np.mean(0.5 * p.alpha * v**2 - 0.25 * p.beta * v**4))
    return {
        "amplitude": amplitude,
        "lam_entropy": p.lam_entropy,
        **st,
        "V_rms": float(np.sqrt(np.mean(v**2))),
        "V_sat_theory": v_sat,
        "mean_energy_density_model_units": e_density,
    }


def run_vacio_continue(
    v0: np.ndarray, p: VacioParams, steps: int, lam_entropy: float
) -> tuple[np.ndarray, dict]:
    p2 = VacioParams(**{**p.__dict__, "lam_entropy": lam_entropy, "steps": steps})
    v = v0.copy()
    for _ in range(steps):
        v = step_vacio(v, p2)
    return v, {**coherence_stats(v, p2.v_th), "lam_entropy": lam_entropy}


def hysteresis_test(p: VacioParams) -> dict:
    rng = np.random.default_rng(1)
    x = np.arange(p.n)
    y = np.arange(p.n)
    X, Y = np.meshgrid(x, y, indexing="ij")
    cx, cy = p.n // 2, p.n // 2
    amp = 0.02
    v = amp * np.exp(-((X - cx) ** 2 + (Y - cy) ** 2) / (0.06 * p.n) ** 2)
    v += 0.15 * amp * rng.standard_normal((p.n, p.n))
    p_hi = VacioParams(**{**p.__dict__, "lam_entropy": 0.50})
    for _ in range(p_hi.steps):
        v = step_vacio(v, p_hi)
    hi = coherence_stats(v, p.v_th)
    hi.update(
        {
            "lam_entropy": 0.50,
            "V_rms": float(np.sqrt(np.mean(v**2))),
            "mean_energy_density_model_units": float(
                np.mean(0.5 * p.alpha * v**2 - 0.25 * p.beta * v**4)
            ),
        }
    )
    v_snap = v.copy()
    p_lo = VacioParams(**{**p.__dict__, "lam_entropy": 0.10})
    for _ in range(p_lo.steps // 2):
        v = step_vacio(v, p_lo)
    lo = coherence_stats(v, p.v_th)
    lo.update(
        {
            "lam_entropy": 0.10,
            "V_rms": float(np.sqrt(np.mean(v**2))),
            "mean_energy_density_model_units": float(
                np.mean(0.5 * p.alpha * v**2 - 0.25 * p.beta * v**4)
            ),
        }
    )
    return {
        "high_entropy_control": hi,
        "low_entropy_after": lo,
        "memory_fraction_V_rms": lo["V_rms"] / max(hi["V_rms"], 1e-12),
    }


def candidate_omega_predictions(p: VacioParams, sim: dict, hyst: dict) -> list[dict]:
    r_crit = (p.phi_star / p.phi_0) ** 2
    r_final = hyst["low_entropy_after"]["R"]
    f_active = sim["frac_active"]
    preds = []

    def add(name: str, formula: str, value: float):
        preds.append(
            {
                "hypothesis": name,
                "formula": formula,
                "Omega_pred": value,
                "delta_vs_Planck": value - OMEGA_L_TARGET,
                "works_without_input": True,
            }
        )

    add("H1_active_area_fraction", "Omega = A_active / A_total", f_active)
    add("H2_phi0_over_phi_star", "Omega = phi_0 / phi_*", p.phi_0 / p.phi_star)
    add("H3_one_over_one_plus_Rcrit", "Omega = 1/(1+R_crit)", 1.0 / (1.0 + r_crit))
    add("H4_Rcrit_over_Rfinal", "Omega = R_crit / R_final", r_crit / max(r_final, 1e-9))
    add("H5_one_minus_sqrt_alpha", "Omega = 1 - sqrt(alpha)", 1.0 - math.sqrt(p.alpha))
    add(
        "H6_saturation_energy_over_max",
        "Omega = <|V|>/V_sat (model units)",
        sim["V_rms"] / sim["V_sat_theory"],
    )
    mem = hyst.get("memory_fraction_V_rms", 0.0)
    add("H8_hysteresis_memory_fraction", "Omega = V_rms_low / V_rms_high", mem)
    add(
        "H7_complement_of_boundary",
        "Omega = 1 - a0/(cH0)  [uses H0,a0 — INPUT]",
        1.0 - (1.20e-10 / (C * H0)),
    )
    return preds


def dimensional_bridge_attempt(p: VacioParams, sim: dict) -> dict:
    """
    Intento de pasar de unidades del modelo VACIO a kg/m^3 sin Planck.
    Solo anclajes internos: V_sat, phi_star, alpha, beta.
    """
    v_sat = math.sqrt(p.alpha / p.beta)
    # Escalado 1: phi_star es adimensional -> no da metros
    rho_from_phi = p.phi_star**4  # adimensional, no SI
    # Escalado 2: identificar energia modelo con rho_crit (ESTO YA ES INPUT COSMOLOGICO)
    e_model = sim["mean_energy_density_model_units"]
    rho_if_identify_crit = e_model * RHO_CRIT / max(abs(e_model), 1e-30)
    return {
        "verdict": "FAIL_without_external_ruler",
        "explanation": (
            "El modelo VACIO no tiene unidad de longitud/tiempo/masa. "
            "phi_star, alpha, beta son numeros puros del grid 128x128. "
            "Para obtener kg/m^3 hay que importar al menos una escala fisica "
            "(H0, a0, l_Planck, o rho_crit)."
        ),
        "model_energy_density": e_model,
        "phi_star_adimensional": p.phi_star,
        "naive_phi_star_to_rho_kg_m3": rho_from_phi,
        "rho_crit_kg_m3_for_reference_only": RHO_CRIT,
    }


def main() -> None:
    p = VacioParams()
    threshold_scan = []
    for amp in [0.001, 0.002, 0.005, 0.01, 0.02, 0.05]:
        threshold_scan.append(run_vacio(amp, p, seed=42))

    activated = [t for t in threshold_scan if t["S"] == 1]
    sim_ref = activated[-1] if activated else threshold_scan[-1]
    hyst = hysteresis_test(p)
    preds = candidate_omega_predictions(p, sim_ref, hyst)
    bridge = dimensional_bridge_attempt(p, sim_ref)

    best = min(preds, key=lambda x: abs(x["delta_vs_Planck"]))
    honest = [x for x in preds if x["hypothesis"] != "H7_complement_of_boundary"]
    best_honest = min(honest, key=lambda x: abs(x["delta_vs_Planck"]))

    report = {
        "camino": 1,
        "title": "VACIO nucleacion/histeresis -> Omega_Lambda",
        "target_Omega_Lambda": OMEGA_L_TARGET,
        "vacio_reference_run": sim_ref,
        "hysteresis": hyst,
        "threshold_scan": threshold_scan,
        "candidate_predictions": preds,
        "best_match_honest": best_honest,
        "best_match_including_input": best,
        "dimensional_bridge": bridge,
        "camino1_verdict": (
            "FAIL as fundamental Lambda mechanism"
            if abs(best_honest["delta_vs_Planck"]) > 0.05
            else "MARGINAL — needs 3D covariant embedding"
        ),
        "simple_summary_es": (
            "VACIO explica COMO se organiza el vacio (burbuja, memoria), "
            "pero sus numeros viven en un mundo sin metros ni segundos. "
            "Ninguna formula solo-VACIO acerto Omega=0.69 sin traer H0 o Planck."
        ),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
