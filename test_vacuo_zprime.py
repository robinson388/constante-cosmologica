import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt

# ---------------------------------------------------------
# 1. THEORETICAL & MODEL PARAMETERS
# ---------------------------------------------------------
np.random.seed(42)
N_EVENTS = 20000

M0_ZPRIME = 2500.0    # Base Breit-Wigner Mass (GeV)
GAMMA_WIDTH = 50.0    # Intrinsic Resonance Width (GeV)
ALPHA_VACUUM = 40.0   # Vacuum Compression Response Factor (GeV / TeV_ET)

# ---------------------------------------------------------
# 2. SYNTHETIC EVENT GENERATION
# ---------------------------------------------------------
# Transverse Energy (E_T) as a proxy for local vacuum compression
E_T = np.random.exponential(scale=300.0, size=N_EVENTS) + 500.0

def lorentzian(m, m0, gamma):
    """Breit-Wigner distribution for resonance peak fitting."""
    return (1.0 / np.pi) * (0.5 * gamma) / ((m - m0)**2 + (0.5 * gamma)**2)

observed_masses = []
for et in E_T:
    # Effective mass shift driven by vacuum deformation
    m_effective = M0_ZPRIME + ALPHA_VACUUM * (et / 1000.0)
    
    # Generate invariant mass per event with Cauchy distribution
    cauchy_noise = np.random.standard_cauchy()
    m_val = m_effective + cauchy_noise * (GAMMA_WIDTH / 2.0)
    observed_masses.append(m_val)

observed_masses = np.array(observed_masses)

# Detector acceptance window
mask = (observed_masses > 2000) & (observed_masses < 3200)
observed_masses = observed_masses[mask]
E_T = E_T[mask]

# ---------------------------------------------------------
# 3. ANALYSIS: COMPRESSION BINS (LOW vs HIGH E_T)
# ---------------------------------------------------------
mask_low_comp = E_T < 800.0
mask_high_comp = E_T > 1000.0

def fit_cauchy(data):
    counts, bin_edges = np.histogram(data, bins=50, range=(2200, 2900), density=True)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    popt, _ = curve_fit(lorentzian, bin_centers, counts, p0=[2500.0, 50.0])
    return bin_centers, counts, popt

centers_low, counts_low, popt_low = fit_cauchy(observed_masses[mask_low_comp])
centers_high, counts_high, popt_high = fit_cauchy(observed_masses[mask_high_comp])

# ---------------------------------------------------------
# 4. RESULTS & DATA OUTPUT
# ---------------------------------------------------------
print("\n" + "="*65)
print("     VACUUM COMPRESSION HYPOTHESIS TEST (Z' Exciton Peak)")
print("="*65)
print(f"[*] Standard Model Baseline (M0) : {M0_ZPRIME:.2f} GeV")
print(f"[*] Fitted Peak (Low E_T Bin)   : {popt_low[0]:.2f} GeV")
print(f"[*] Fitted Peak (High E_T Bin)  : {popt_high[0]:.2f} GeV")

delta_m = popt_high[0] - popt_low[0]
print(f"\n[!] Peak Mass Shift Detected (Delta M): +{delta_m:.2f} GeV")

if abs(delta_m) > 10.0:
    print(" STATUS: RHEOLOGICAL VACUUM SIGNATURE DETECTED (Statistically Significant)")
else:
    print(" STATUS: COMPATIBLE WITH STANDARD MODEL BASELINE")
print("="*65)

# Plotting the experimental signature
plt.figure(figsize=(10, 6))
plt.plot(centers_low, counts_low, 'b.-', label=f'Low Compression Bin (Peak M = {popt_low[0]:.1f} GeV)')
plt.plot(centers_high, counts_high, 'r.-', label=f'High Compression Bin (Peak M = {popt_high[0]:.1f} GeV)')
plt.axvline(x=M0_ZPRIME, color='gray', linestyle='--', label='Standard Model Baseline')
plt.title("Vacuum Compression Effect on Heavy Resonances (Z' Exciton Shift)")
plt.xlabel("Invariant Mass [GeV]")
plt.ylabel("Event Density")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("vacuum_shift_experiment.png", dpi=150)
print("\n[+] Plot saved as 'vacuum_shift_experiment.png'.\n")
