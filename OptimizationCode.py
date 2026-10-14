"""
ENAE 410 - illustrative design sweeps (Stage 7 of the Mathematical Design Procedure).

Every input in the INPUTS block carries a data-status label:
  [M] measured  [C] course data  [A] assumption  [I] illustrative placeholder
Replace placeholders with measured values, rerun, and relabel figures accordingly.
Run:  python enae410_sweeps.py      -> figures written to ./figures
Equations: ENAE 410 Midterm F2026 formula sheet and Design Lab 1 (mass scaling).
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ============================ INPUTS ============================
g = 9.81
RHO = 1.10            # [A] ISA at ~1050 m; confirm field elevation/temperature
MU = 1.76e-5          # [A] dynamic viscosity, Pa*s (~8 C)
M_FIXED_G = 94.9      # [C] Lab 1 component list; replace with weighed kit [M]
M_MISC_G = 10.0       # [A] wires, pushrods, hinges, glue
M_TARGET = 0.220      # [A] design mass target, kg
S_BASE, AR_BASE = 0.12, 6.0   # [I] placeholder baseline
CLMAX = 1.0           # [C]/[A] Lab 1 wind-tunnel CLmax 1.075, rounded down
CD0, E_OSW = 0.050, 0.80      # [C]/[A] Lab 1 fit CD0 ~0.054; e = 0.8 (Lab 3)
K_LAUNCH = 1.3        # [A]
# Thrust available vs airspeed, gf. [C] approximate read-off of Lab 1 Fig. 3 (MotoCalc).
# Replace with the D2L spreadsheet values and anchor V=0 to measured static thrust [M].
THRUST = {"100%": [(0, 182), (5, 160), (10, 136), (15, 108), (20, 70), (23, 35), (24, 0)],
          "80%":  [(0, 142), (5, 125), (10, 103), (15, 75), (20, 25), (21, 0)],
          "60%":  [(0, 95), (5, 80), (10, 55), (14, 15), (15, 0)]}
# Lab 1 mass-scaling reference [C]
B_REF, S_REF, SA_REF, VOL_REF, RHO_MAT = 0.19948, 0.00631753, 0.02207, 3.8292e-5, 800.0
WALLS_MM = [0.30, 0.40]   # [A] replace with coupon-derived equivalent thickness [M]
INFILL = 0.0              # [A]
FIELD_RALLOW = {"64 m wide": 22.0, "45 m usable": 12.5}   # [I] (W_u - 2*c_e)/2 with c_e = 10 m
# ================================================================

OUT = "figures"; os.makedirs(OUT, exist_ok=True)
COL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]

def stall_speed(m, S, clmax, rho=RHO):            # formula sheet, steady level flight at CLmax
    return np.sqrt(2 * m * g / (rho * S * clmax))

def load_factor(phi_deg):                         # n = 1/cos(phi)
    return 1 / np.cos(np.radians(phi_deg))

def turn_radius(V, phi_deg):                      # R = V^2/(g tan phi)
    return V**2 / (g * np.tan(np.radians(phi_deg)))

def K_factor(AR, e=E_OSW):                        # K = 1/(pi e AR)
    return 1 / (np.pi * e * AR)

def drag_gf(V, m, S, AR, n=1.0, cd0=CD0, rho=RHO):  # D = qS CD0 + K (nW)^2/(qS)
    q = 0.5 * rho * V**2
    return (q * S * cd0 + K_factor(AR) * (n * m * g)**2 / (q * S)) / g * 1000

def thrust_avail_gf(V, setting):
    v, t = zip(*THRUST[setting]); return np.interp(V, v, t)

def mass_from_span(b, wall_mm, infill=INFILL):    # Lab 1 section 2.4
    r = b / B_REF
    m_struct = infill * RHO_MAT * VOL_REF * r**3 + RHO_MAT * wall_mm / 1000 * SA_REF * r**2
    return M_FIXED_G + M_MISC_G + m_struct * 1000, S_REF * r**2

def fig_stall():
    S = np.linspace(0.06, 0.22, 200); plt.figure(figsize=(6.2, 3.3))
    for i, m in enumerate([0.18, 0.22, 0.2499]):
        plt.plot(S, stall_speed(m, S, CLMAX), color=COL[i], label=f"{m*1000:.0f} g, CLmax {CLMAX}")
    for ls, cl in [("--", 0.8), (":", 1.2)]:
        plt.plot(S, stall_speed(M_TARGET, S, cl), color=COL[1], ls=ls, label=f"{M_TARGET*1000:.0f} g, CLmax {cl}")
    plt.xlabel("Wing area S (m²)"); plt.ylabel("Vs (m/s)"); plt.legend(fontsize=7); plt.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(f"{OUT}/1_stall_vs_area.png", dpi=200); plt.close()

def fig_turn():
    V = np.linspace(5, 14, 200); plt.figure(figsize=(6.2, 3.3))
    for i, p in enumerate([15, 25, 35]):
        plt.plot(V, turn_radius(V, p), color=COL[i], label=f"φ = {p}°")
    for k, r in FIELD_RALLOW.items():
        plt.axhline(r, color="#52514e", ls="--", lw=1); plt.text(5, r + 0.8, f"R_allow {r} m ({k})", fontsize=7)
    plt.ylim(0, 60); plt.xlabel("Airspeed (m/s)"); plt.ylabel("R (m)"); plt.legend(); plt.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(f"{OUT}/2_turn_radius.png", dpi=200); plt.close()

def fig_turn_stall():
    ph = np.linspace(0, 60, 200); plt.figure(figsize=(6.2, 3.0))
    plt.plot(ph, np.sqrt(load_factor(ph)), color=COL[0], label="Vs,turn / Vs = √n")
    plt.plot(ph, load_factor(ph), color=COL[1], label="n")
    plt.xlabel("Bank angle (deg)"); plt.ylabel("Ratio (-)"); plt.legend(); plt.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(f"{OUT}/3_turn_stall.png", dpi=200); plt.close()

def fig_thrust():
    V = np.linspace(5.5, 20, 300); plt.figure(figsize=(6.2, 3.4))
    for i, k in enumerate(THRUST):
        v, t = zip(*THRUST[k]); plt.plot(v, t, color=COL[2 + i], lw=1.5, label=f"Available {k}")
    plt.plot(V, drag_gf(V, M_TARGET, S_BASE, AR_BASE), color=COL[0], label="Required, level")
    plt.plot(V, drag_gf(V, M_TARGET, S_BASE, AR_BASE, n=load_factor(30)), color=COL[1], label="Required, 30° bank")
    plt.axvline(K_LAUNCH * stall_speed(M_TARGET, S_BASE, CLMAX), color="#52514e", ls="--", lw=1)
    plt.xlabel("Airspeed (m/s)"); plt.ylabel("Thrust (gf)"); plt.legend(fontsize=7); plt.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(f"{OUT}/4_thrust.png", dpi=200); plt.close()

def fig_ld():
    CL = np.linspace(0.05, 1.2, 200); plt.figure(figsize=(6.2, 3.2))
    cands = {"A conventional": (0.050, 0.80, 6, 1.0), "B glider-like": (0.045, 0.85, 9, 1.0), "C flying wing": (0.040, 0.75, 5, 0.8)}  # [A]
    for i, (k, (cd0, e, AR, clm)) in enumerate(cands.items()):
        c = CL[CL <= clm]; K = K_factor(AR, e); plt.plot(c, c / (cd0 + K * c**2), color=COL[i], label=k)
        print(f"{k}: (L/D)max = {1/(2*np.sqrt(cd0*K)):.2f} at CL = {np.sqrt(cd0/K):.2f}")
    plt.xlabel("CL"); plt.ylabel("L/D"); plt.legend(fontsize=7); plt.grid(alpha=.3)
    plt.tight_layout(); plt.savefig(f"{OUT}/5_LD.png", dpi=200); plt.close()

def fig_span():
    b = np.linspace(0.55, 1.15, 200); fig, ax = plt.subplots(1, 2, figsize=(6.4, 2.9))
    for i, t in enumerate(WALLS_MM):
        m, S = mass_from_span(b, t)
        ax[0].plot(b, m, color=COL[i], label=f"wall {t} mm"); ax[1].plot(b, stall_speed(m / 1000, S, CLMAX), color=COL[i])
    ax[0].axhline(249.9, color="#e34948", ls="--", lw=1); ax[0].set_xlabel("Span (m)"); ax[0].set_ylabel("Total mass (g)"); ax[0].legend(fontsize=7)
    ax[1].set_xlabel("Span (m)"); ax[1].set_ylabel("Vs (m/s)")
    fig.tight_layout(); fig.savefig(f"{OUT}/6_span_mass.png", dpi=200); plt.close()

if __name__ == "__main__":
    vs = stall_speed(M_TARGET, S_BASE, CLMAX)
    print(f"Baseline Vs = {vs:.2f} m/s, launch >= {K_LAUNCH*vs:.2f} m/s, W/S = {M_TARGET*g/S_BASE:.1f} N/m^2")
    fig_stall(); fig_turn(); fig_turn_stall(); fig_thrust(); fig_ld(); fig_span()
    print(f"Figures written to ./{OUT}")