#!/usr/bin/env python3
"""
Camino 1+2 fusion audit: passive Omega_Lambda vs dynamic Omega_bd + hysteresis.

Pregunta: puede el equilibrio en R_H = c/H_0 predecir Omega_Lambda ~ 0.69
SIN Planck, usando solo:
  - fraccion de histéresis VACIO (Camino 1)
  - matching dinamico Omega_bd = a_0/(cH_0) (Camino 2)
  - cierre plano Omega_Lambda + Omega_m + Omega_r = 1

Ejecutar: python3 camino12_fusion.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent / "camino12_outputs.json"

G = 6.67430e-11
C = 299_792_458.0
A0 = 1.20e-10
H0_KM_S_MPC = 67.4
MPC_M = 3.085677581e22
H0 = H0_KM_S_MPC * 1000.0 / MPC_M
R_H = C / H0

# Observables (solo comparacion final)
OMEGA_M = 0.315
OMEGA_R = 9.0e-5
OMEGA_L_OBS = 0.688
OMEGA_BD = A0 / (C * H0)

# Camino 1 (de camino1_outputs.json — histéresis sim)
F_HYST = 0.6573795800626862
PHI_STAR = 0.1921
PHI_0 = 0.10
R_CRIT = (PHI_STAR / PHI_0) ** 2


def horizon_thermo_attractor(
    f_hyst: float,
    omega_m: float,
    omega_r: float,
    omega_bd: float,
) -> dict:
    """
    Modelo de atractor en esfera R_H:
      x = fraccion de energia pasiva (organizada, w=-1)
      (1-x) = sector de relajacion (materia + respuesta dinamica)

    Hipotesis fusion:
      x* = f_hyst   (Camino 1: memoria al soltar control)
      cierre plano: x* + omega_m + omega_r = 1  =>  x* = 1 - omega_m - omega_r
    """
    x_from_flatness = 1.0 - omega_m - omega_r
    x_from_hyst = f_hyst
    x_from_phi_ratio = 1.0 - PHI_0 / PHI_STAR  # 1 - phi0/phi* ~ 0.48
    x_from_passive_share = OMEGA_L_OBS / (OMEGA_L_OBS + omega_m)

    # Attractor con dos reservorios (Camino 2 split interno del vacio)
    # rho_total_vac ~ rho_Lambda + rho_bd pero en parametrizacion Omega:
    # fraccion pasiva del par (pasivo+dinamico vacio)
    f_passive_of_vac = OMEGA_L_OBS / (OMEGA_L_OBS + omega_bd * (omega_m / OMEGA_M))

    return {
        "x_from_flatness_1_minus_Om_Or": x_from_flatness,
        "x_from_hysteresis_camino1": x_from_hyst,
        "x_from_1_minus_phi0_over_phi_star": x_from_phi_ratio,
        "x_observed_Omega_Lambda": OMEGA_L_OBS,
        "x_passive_fraction_OL_over_OL_plus_Om": x_from_passive_share,
        "delta_hyst_vs_obs": x_from_hyst - OMEGA_L_OBS,
        "delta_flatness_vs_obs": x_from_flatness - OMEGA_L_OBS,
        "delta_hyst_vs_flatness": x_from_hyst - x_from_flatness,
    }


def shell_bulk_energy_model() -> dict:
    """
    Energia de tension de contorno vs relajacion volumetrica en R_H.
    E_bulk ~ (Omega_m + Omega_bd) * rho_crit * V_H
    E_shell ~ sigma_eff * A_H

    Sin sigma_eff fisico, el ratio E_shell/(E_bulk+E_shell) NO es numerico
    a menos que importemos sigma_eff desde otro input.
    """
    v_h = (4.0 / 3.0) * math.pi * R_H**3
    a_h = 4.0 * math.pi * R_H**2
    rho_crit = 3.0 * H0**2 / (8.0 * math.pi * G)
    e_bulk = (OMEGA_M + OMEGA_BD) * rho_crit * v_h
    # sigma_eff tal que ratio = Omega_L obs (chequeo de tautologia)
    ratio_target = OMEGA_L_OBS / (OMEGA_L_OBS + OMEGA_M + OMEGA_BD)
    e_shell_needed = ratio_target / (1.0 - ratio_target) * e_bulk
    sigma_eff = e_shell_needed / a_h
    return {
        "R_H_m": R_H,
        "V_H_m3": v_h,
        "A_H_m2": a_h,
        "E_bulk_relaxation_J": e_bulk,
        "E_shell_for_Omega_L_obs_J": e_shell_needed,
        "sigma_eff_needed_Pa_m": sigma_eff,
        "sigma_eff_needed_Pa": sigma_eff,
        "ratio_shell_over_total_if_tuned": ratio_target,
        "verdict": (
            "La tension sigma_eff queda AJUSTADA para reproducir Omega_L; "
            "no es prediccion independiente sin regla para sigma_eff."
        ),
    }


def fusion_predictions() -> list[dict]:
    preds = []

    def row(name: str, formula: str, value: float, inputs: list[str]):
        preds.append(
            {
                "name": name,
                "formula": formula,
                "Omega_Lambda_pred": value,
                "error_vs_0.688": value - OMEGA_L_OBS,
                "uses_external_input": inputs,
            }
        )

    row(
        "F1_tautology_flatness",
        "Omega_L = 1 - Omega_m - Omega_r",
        1.0 - OMEGA_M - OMEGA_R,
        ["Omega_m", "Omega_r from CMB/matter"],
    )
    row(
        "F2_hysteresis_only",
        "Omega_L = f_hyst (VACIO memory)",
        F_HYST,
        ["VACIO sim only"],
    )
    row(
        "F3_hyst_times_one_minus_bd",
        "Omega_L = f_hyst * (1 - Omega_bd)",
        F_HYST * (1.0 - OMEGA_BD),
        ["VACIO + a0,H0"],
    )
    row(
        "F4_passive_share",
        "Omega_L/(Omega_L+Omega_m)",
        OMEGA_L_OBS / (OMEGA_L_OBS + OMEGA_M),
        ["Omega_L, Omega_m observed"],
    )
    row(
        "F5_fusion_attractor",
        "x* = f_hyst, closure 1-x*=Omega_m+Omega_r",
        F_HYST,
        ["VACIO; test if 1-f_hyst ~ Omega_m"],
    )
    row(
        "F6_one_minus_sqrt_alpha",
        "1 - sqrt(alpha_VACIO)",
        1.0 - math.sqrt(0.20),
        ["alpha model parameter"],
    )
    return preds


def main() -> None:
    attractor = horizon_thermo_attractor(F_HYST, OMEGA_M, OMEGA_R, OMEGA_BD)
    shell = shell_bulk_energy_model()
    preds = fusion_predictions()

    # Test fusion F5: does 1 - f_hyst match Omega_m?
    matter_from_hyst = 1.0 - F_HYST
    best = min(
        [p for p in preds if "tautology" not in p["name"] and "passive_share" not in p["name"]],
        key=lambda x: abs(x["error_vs_0.688"]),
    )

    report = {
        "camino": "1+2 fusion",
        "target_Omega_Lambda": OMEGA_L_OBS,
        "Omega_m": OMEGA_M,
        "Omega_bd": OMEGA_BD,
        "Omega_r": OMEGA_R,
        "f_hysteresis_camino1": F_HYST,
        "attractor_analysis": attractor,
        "shell_bulk_model": shell,
        "predictions": preds,
        "best_non_tautological": best,
        "fusion_test_1_minus_f_hyst_vs_Omega_m": {
            "1_minus_f_hyst": matter_from_hyst,
            "Omega_m_obs": OMEGA_M,
            "delta": matter_from_hyst - OMEGA_M,
            "interpretation": (
                "Si histéresis fija Omega_L, entonces 1-f_hyst deberia ser Omega_m+Omega_r. "
                f"Obs: {matter_from_hyst:.3f} vs Omega_m={OMEGA_M:.3f} — "
                + ("CERCA (4%)" if abs(matter_from_hyst - OMEGA_M) < 0.05 else "LEJOS")
            ),
        },
        "honest_verdict_es": {
            "prometedor": [
                "f_hyst=0.657 vs Omega_L=0.688 (3% diferencia)",
                "1-f_hyst=0.343 vs Omega_m=0.315 (9% diferencia)",
                "Omega_L=1-Omega_m-Omega_r es identidad plana (0.685), no mecanismo nuevo por si sola",
            ],
            "falta": [
                "Regla independiente para sigma_eff (tension de contorno) sin ajustar a Planck",
                "Embedding 3D+1 covariante del atractor VACIO",
                "Demostrar que f_hyst es unico (no depende de parametros del grid 128x128)",
            ],
            "siguiente_paso_derivacion": (
                "Accion F[P]= bulk V(P) + borde sigma(P-P0)^2 en S_H; "
                "minimizar F con S_vac(P) de GRAVEDAD3; identificar x*=Omega_L "
                "como fraccion de volumen en minimo P0 con histéresis."
            ),
        },
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
