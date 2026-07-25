# Constante cosmológica — IR matching EFT (`paper_lambda`)

Manuscrito independiente de **GRAVEDAD3** (paper covariante) y **cromatic2** (canal EM).  
Este repositorio contiene solo el note sobre matching IR de $\Lambda$ en un EFT de respuesta de vacío clásico.

**Título:** *IR Matching of the Cosmological Constant in a Classical Vacuum-Response EFT*  
**Fuente LaTeX:** `paper_lambda.tex`  
**PDF:** `paper_lambda.pdf` (regenerable con `bash compile.sh`)

Compañeros citados en el texto (otros repos / Zenodo): GRAVEDAD3, cromatic2, VACIO.

## Inicio rápido

```bash
pip install -r requirements.txt
bash const              # alias: run_all.sh quick (~30 s)
python3 verify_outputs.py
bash constd             # alias: compilar PDF
```

## Reproducibilidad numérica

```bash
bash run_all.sh quick      # CI / revisión rápida
bash run_all.sh standard   # + pipeline fusion
bash run_all.sh full       # + PDE VACIO 2D/3D (lento, ~8 GB RAM)
python3 verify_outputs.py
```

| Script | Output | Sección paper |
|--------|--------|---------------|
| `calcular_rho_vac.py` | stdout JSON | Eq. numbers |
| `derivar_sigma_eff.py` | `camino12_sigma_outputs.json` | $\sigma_{\rm eff}$ |
| `camino12_chi_Svac.py` | `camino12_chi_Svac_outputs.json` | Eq. chi sector |
| `camino12_Svac_cubic.py` | `camino12_Svac_cubic_outputs.json` | Apéndice cúbico |
| `camino12_fusion.py` | `camino12_outputs.json` | Camino 1+2 |
| `camino12_pipeline.py` | `camino12_pipeline_outputs.json` | Pipeline audit |
| `camino1_vacio_lambda.py` | `camino1_outputs.json` | VACIO 2D |
| `camino12_vacio_3d.py` | `camino12_vacio_3d_outputs.json` | Null test 3D |
| `test2_sparc_field.py` | `test2_sparc_field_outputs.json` | Test 2 AQUAL |
| `test4_spherical_core.py` | `test4_spherical_core_outputs.json` | Test 4 core |

Golden checks: `expected_outputs/manifest.json` + `verify_outputs.py`.

Referencia histórica del Test 4: `reference/attack_gr_bh_derived.py` (prototipo GRAVEDAD3, no requerido para CI).

## Requisitos

- Python **3.10+**, numpy, scipy
- LaTeX (pdflatex + revtex4-2) solo para PDF

## GitHub Actions

`.github/workflows/reproduce.yml` ejecuta `run_all.sh quick` en cada push.

## Publicar en GitHub

```bash
gh auth login          # una sola vez
bash publish_github.sh # repo: constante-cosmologica
```

## Documentos de envío PRD

- `APS_PRD_CHECKLIST.md`
- `COVER_LETTER_PRD.md`

## Cita

R. Bueno Parra, *IR Matching of the Cosmological Constant in a Classical Vacuum-Response EFT* (2026).
