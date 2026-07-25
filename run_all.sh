#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# 
# EFMVR / Phase Cosmology Master Execution Pipeline
# Purpose: Automatically run the full analytical cascade in the exact order
#          of physical and computational dependencies.
#

# Exit immediately if any command exits with a non-zero status
set -e

echo "================================================================="
echo "  STARTING COMPLETE EFMVR COSMOLOGICAL PIPELINE RUN"
echo "================================================================="

# Step 1: Execute the dynamic ab-initio quartic-horizon extraction
echo -e "\n[STEP 1/3] Extracting dynamic attractor parameters..."
python3 atractor_mecanico_puro.py

# Step 2: Inject the extracted x_star payload into the Bayesian priors configuration
echo -e "\n[STEP 2/3] Injecting mechanical values into Bayesian tree..."
python3 inject_mechanical_closure.py

# Step 3: Run marginalized posterior analyses and tensor mass bridges
echo -e "\n[STEP 3/3] Running posterior analyzer and tensor mass bridges..."
python3 phase_d_analyze_posteriors.py
python3 cazar_graviton_mass_limit.py
python3 plot_mcmc_contours.py
python3 export_tables.py
python3 count_neff34_channels.py
python3 planck_eft_residual_test.py

echo -e "\n================================================================="
echo "  PIPELINE EXECUTION SUCCESSFUL - ALL ARTIFACTS VERIFIED"
echo "================================================================="
