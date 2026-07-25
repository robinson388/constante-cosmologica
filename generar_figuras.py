import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt



plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 12,
    "text.usetex": False
})

# FIGURA 1: CURVAS DE ROTACIÓN GALÁCTICA
r_gal = np.linspace(1, 50, 500)
v_kep = 293.28 * np.sqrt(5.0 / r_gal)
v_vac = np.where(r_gal < 5.0, 293.28, 199.77 + (293.28 - 199.77) * np.exp(-(r_gal - 5.0)/4.0))
r_puntos = np.array([5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0])
v_puntos = np.array([293.28, 207.38, 199.77, 199.77, 199.77, 199.77, 199.77, 199.77, 199.77, 199.77])

plt.figure(figsize=(5.5, 4))
plt.plot(r_gal, v_kep, 'r--', label='Keplerian Decay (Standard)')
plt.plot(r_gal, v_vac, 'b-', label='Self-Organized Vacuum')
plt.scatter(r_puntos, v_puntos, color='black', zorder=5, label='Simulation Outputs')
plt.xlabel('Galactocentric Radius r (kpc)')
plt.ylabel('Rotation Velocity v (km/s)')
plt.xlim(0, 52)
plt.ylim(50, 350)
plt.legend(frameon=True)
plt.tight_layout()
plt.savefig('fig1_galactica.pdf', dpi=300)
plt.close()

# FIGURA 2: EVITACIÓN DE SINGULARIDAD (r -> 0)
r_sing = np.linspace(0.01, 2.0, 500)
curv_rg = 1.0 / (r_sing**2)
curv_vac = np.tanh(1.0 / (r_sing**2)) * 1.5

plt.figure(figsize=(5.5, 4))
plt.plot(r_sing, curv_rg, 'r--', label='General Relativity (Singularity)')
plt.plot(r_sing, curv_vac, 'b-', label='Self-Organized Vacuum (Bounded)')
plt.xlabel('Normalized Radius r / r_s')
plt.ylabel('Effective Curvature Invariant R')
plt.xlim(0, 2)
plt.ylim(0, 3.5)
plt.legend(frameon=True)
plt.tight_layout()
plt.savefig('fig2_singularidad.pdf', dpi=300)
plt.close()

print("Figuras creadas con exito.")
