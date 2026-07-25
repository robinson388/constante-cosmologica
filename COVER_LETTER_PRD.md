# Cover Letter — Physical Review D

**Manuscript:** *IR Matching of the Cosmological Constant in a Classical Vacuum-Response EFT*  
**Author:** Robinson Bueno Parra  
**Suggested section:** General Relativity and Cosmology  

---

Dear Editor,

Please consider the enclosed manuscript for publication in *Physical Review D*.

**Scope.** The paper separates three layers often conflated in modified-gravity drafts: (i) a covariant classical scalar–tensor effective field theory for a vacuum-response field; (ii) a constitutive infrared matching between the galactic scale $a_0$ and the Hubble scale $H_0$; and (iii) a passive $\Lambda$CDM background fixed by CMB data. It does **not** claim a quantum derivation of $\Omega_\Lambda$.

**Connection to established observables (desk-review checklist).**  
Parameters are anchored to published data cited in Sec. I B:
- Planck 2018: $H_0=67.4\,\mathrm{km\,s^{-1}\,Mpc^{-1}}$, $\Omega_\Lambda=0.688$, $\Omega_m=0.315$
- MOND/SPARC: $a_0=1.2\times10^{-10}\,\mathrm{m/s^2}$
- Cassini PPN: $\gamma-1=(2.1\pm2.3)\times10^{-5}$
- GW170817: $v_{\rm gw}=c$

**Falsifiable outputs (not merely fitted narratives).**
1. Horizon attractor fraction $x_\star$ from $H_0$ and entropy data without $\Omega_\Lambda$ in the $\chi$ sector (current post-diction $\sim0.689$ vs.\ Planck $0.688$; sensitivity in Appendix A).
2. Null test: volumetric 3D hysteresis overshoots $\Omega_\Lambda$ by $\sim20\%$; holographic 2D closure is the viable channel (Appendix B).
3. Integrated AQUAL galactic rotation from the scalar gradient law (Appendix C; script `test2_sparc_field.py`).
4. Core regularization from quartic $V(P)$ integration, not a manual saturation ansatz (Appendix D).

**Reproducibility.** All numerical benchmarks are regenerated via `bash run_all.sh quick` (GitHub-ready bundle in `paper_constante_cosmologica/`).

**Companion Zenodo records** (data/preprint companions, fully cited with DOI) support tensor and electromagnetic channels but are not required to follow the $\Lambda$ closure in this manuscript.

We believe the work fits PRD’s interest in modified gravity, cosmology, and explicit observational contact, with honest scope limits stated in the Abstract and Sec. VI.

Sincerely,

Robinson Bueno Parra  
robinbuenoparra8@gmail.com  
Independent Researcher, Spain
