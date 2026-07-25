#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EFMVR LaTeX Table Exporter Pipeline
Purpose: Generate clean, publication-ready LaTeX tabular macros
         with double-column table* encapsulation.
"""

import json
import os
import sys

SUMMARY_JSON = "attack_gr_outputs/evidence/phase_d_getdist_summary.json"
TENSOR_JSON = "attack_gr_outputs/mg_upper_limit_eV.json"
OUTPUT_TEX = "attack_gr_outputs/evidence/manuscript_tables.tex"

print("=== RUNNING LATEX TABLE EXPORTER ===")

if not os.path.exists(SUMMARY_JSON) or not os.path.exists(TENSOR_JSON):
    print("[ERROR] Required pipeline JSON outputs are missing.")
    sys.exit(1)

with open(SUMMARY_JSON, "r") as f:
    metrics = json.load(f)
with open(TENSOR_JSON, "r") as f:
    tensor = json.load(f)

h0_star = metrics["posteriors_68_CL"]["H0_star"]["mean"]
h0_local = metrics["posteriors_68_CL"]["H0_local_eff"]["mean"]
m_g = tensor["mg_upper_limit_eV"]
lambda_g = tensor["lambda_g_km"]

latex_content = f"""% Generated automatically by export_tables.py.
\\newcommand{{\\EFMVRHZeroStar}}{{{h0_star:.2f}}}
\\newcommand{{\\EFMVRHZeroLocal}}{{{h0_local:.2f}}}
\\newcommand{{\\EFMVRGravitonMass}}{{{m_g:.2e}}}
\\newcommand{{\\EFMVRComptonWavelength}}{{{lambda_g:.2e}}}

\\begin{{table*}}[t]
\\caption{{EFMVR Pipeline Statistical Summary, Phase D Posteriors, 
and Observational Benchmarks.}}
\\label{{tab:efmvr_metrics}}
\\centering
\\begin{{tabular}}{{llll}}
\\hline
Parameter & Target Channel & EFMVR Value & Benchmark \\\\
\\hline
$H_0^\\star$ & Global LSS / CMB & 
$\\EFMVRHZeroStar\\ \\mathrm{{km\\ s^{{-1}}\\ Mpc^{{-1}}}}$ & 
$\\approx 67.4$ (Planck) \\\\
$H_{{local,\\ e\\!f\\!f}}^0$ & Local Ladder / Cepheid & 
$\\EFMVRHZeroLocal\\ \\mathrm{{km\\ s^{{-1}}\\ Mpc^{{-1}}}}$ & 
$\\approx 73.0$ (SH0ES) \\\\
$m_g$ & Tensor Birefringence & 
$\\le \\EFMVRGravitonMass\\ \\mathrm{{eV/c^2}}$ & 
$\\le 1.76 \\times 10^{{-23}}$ \\\\
$\\lambda_g$ & Effective Compton & 
$\\ge \\EFMVRComptonWavelength\\ \\mathrm{{km}}$ & 
$\\approx 7.00 \\times 10^{{12}}$ \\\\
\\hline
\\end{{tabular}}
\\end{{table*}}
"""

os.makedirs(os.path.dirname(OUTPUT_TEX), exist_ok=True)
with open(OUTPUT_TEX, "w") as f:
    f.write(latex_content)

print(f"[SUCCESS] LaTeX tables macro exported to: {OUTPUT_TEX}")
