#!/usr/bin/env bash
# Compilar paper_lambda.tex -> paper_lambda.pdf (+ alias constd.pdf local)
set -euo pipefail
cd "$(dirname "$0")"

PUBLISH="${PUBLISH:-1}"
TEX="paper_lambda.tex"
if [[ -d "/mnt/c/Users/robin/Downloads" ]]; then
  OUT_PDF="/mnt/c/Users/robin/Downloads/paper_lambda.pdf"
else
  OUT_PDF="$(cd .. && pwd)/paper_lambda.pdf"
fi

for f in fig1_galactica.pdf fig2_singularidad.pdf; do
  if [[ ! -f "$f" ]]; then
    echo "Generando figuras ($f ausente)..."
    python3 generar_figuras.py
    break
  fi
done

echo "=== const: $TEX -> paper_lambda.pdf ==="
rm -f paper_lambda.aux paper_lambda.out paper_lambda.log

pdflatex -interaction=nonstopmode "$TEX" >/tmp/const_pass1.log 2>&1
pdflatex -interaction=nonstopmode "$TEX" >/tmp/const_pass2.log 2>&1
pdflatex -interaction=nonstopmode "$TEX" | tee /tmp/const_pass3.log

[[ -f paper_lambda.pdf ]] || { echo "ERROR: paper_lambda.pdf no generado"; exit 1; }

cp -f paper_lambda.pdf constd.pdf

if [[ "$PUBLISH" == "1" ]]; then
  cp -f paper_lambda.pdf "$OUT_PDF"
  echo ""
  echo "Publicado:"
  echo "  $(pwd)/paper_lambda.pdf"
  echo "  $(pwd)/constd.pdf"
  echo "  $OUT_PDF"
  ls -lh paper_lambda.pdf constd.pdf "$OUT_PDF" 2>/dev/null || ls -lh paper_lambda.pdf constd.pdf
else
  echo "OK -> paper_lambda.pdf (+ constd.pdf alias)"
  ls -lh paper_lambda.pdf constd.pdf
fi
