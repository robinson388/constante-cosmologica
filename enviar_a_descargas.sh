#!/bin/bash
echo "=== const: paper_lambda.tex -> paper_lambda.pdf ==="
pdflatex paper_lambda.tex && pdflatex paper_lambda.tex

# Comando de copiado real hacia las descargas de Windows
cp paper_lambda.pdf /mnt/c/Users/robin/Downloads/
echo "PDF enviado con exito a las descargas de Windows."
