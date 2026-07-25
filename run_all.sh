#!/usr/bin/env bash
# Reproducibilidad paper_lambda — ejecutar desde paper_constante_cosmologica/
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-standard}"
echo "=== paper_lambda reproducibility (mode=$MODE) ==="

run() {
  echo ""
  echo ">>> $*"
  python3 "$@"
}

# --- Tier A: analiticos / rapidos (< 1 min) ---
run calcular_rho_vac.py
run derivar_sigma_eff.py
run camino12_chi_Svac.py
run camino12_Svac_cubic.py
run test2_sparc_field.py
run test4_spherical_core.py

if [[ "$MODE" == "quick" ]]; then
  python3 verify_outputs.py
  echo "=== QUICK REPRODUCE OK ==="
  exit 0
fi

# --- Tier B: pipeline + fusion ---
run camino12_fusion.py
run camino12_pipeline.py

if [[ "$MODE" == "standard" ]]; then
  python3 verify_outputs.py
  echo "=== STANDARD REPRODUCE OK ==="
  exit 0
fi

if [[ "$MODE" == "full" ]]; then
  run camino1_vacio_lambda.py
  run camino12_vacio_3d.py
  python3 verify_outputs.py
  echo "=== FULL REPRODUCE OK ==="
  exit 0
fi

echo "Unknown mode: $MODE (use quick|standard|full)" >&2
exit 2
