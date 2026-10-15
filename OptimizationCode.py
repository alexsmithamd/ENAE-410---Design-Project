"""
ENAE 410 - illustrative design sweeps (Stage 7 of the Mathematical Design Procedure).

Every input in the INPUTS block carries a data-status label:
  [M] measured  [C] course data  [A] assumption  [I] illustrative placeholder
Replace placeholders with measured values, rerun, and relabel figures accordingly.
Run:  python enae410_sweeps.py      -> figures written to ./figures
Equations : ENAE 410 Midterm F2026 formula sheet and Design Lab 1 (mass scaling).
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
S_BASE, AR_BASE = 0.03, 6.75   # [I] placeholder baseline
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
# --- NACA 4-digit airfoil selection ---
V_CRUISE = 8.0        # [A] cruise airspeed, m/s (~1.5 Vs at baseline)
TURN_BANK = 30        # [A] design bank angle for the field circuit, deg
CD0_REST = 0.030      # [A] non-wing parasite drag (fuselage, tails, gear), referenced to S
LIFT_SLOPE_FAC = 0.90 # [A] section lift slope = 0.9 * 2pi at Re ~ 7e4 (laminar bubble)
T_MIN_PRINT = 0.08    # [A] min t/c that prints cleanly in LW-PLA and fits a spar
CM_MAX = 0.12         # [A] |cm_c/4| cap so the tail trim load / trim drag stays small
W_SCORE = {"LD": 0.40, "CLmax": 0.45, "cm": 0.15}    # [A] weights (min-max normalised); low Vs matters most for hand launch
CANDIDATES = ["4412", "0012"] + [f"{m}{p}{t:02d}" for m in (2, 3, 4, 5, 6) for p in (3, 4) for t in (6, 8, 9, 10, 12)]
# --- Top-down layout ---
TAPER = 0.70          # [A] tip/root chord; straight quarter-chord line
V_H, V_V = 0.50, 0.04 # [A] tail volume coefficients (typical RC trainer)
AR_H, AR_V = 4.0, 1.5 # [A] horizontal / vertical tail aspect ratio
TAIL_ARM = 0.40       # [A] wing ac -> tail ac, m
X_LE_ROOT = 0.12      # [A] motor face -> wing root LE, m
FUSE_W = 0.040        # [A] max fuselage width, m
PROP_D = 0.127        # [A] propeller diameter, m (5 in); replace with kit prop [M]
STATIC_MARGIN = 0.10  # [A] fraction of MAC
PRINT_BED = 0.220     # [A] printer bed max dimension, m (wing panels split to fit)
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

# ===================== NACA 4-digit selection =====================
def camber(x, m, p):                              # NACA 4-digit mean line and slope
    if m == 0 or p == 0: return np.zeros_like(x), np.zeros_like(x)
    f = x < p
    yc = np.where(f, m / p**2 * (2*p*x - x**2), m / (1 - p)**2 * ((1 - 2*p) + 2*p*x - x**2))
    return yc, np.where(f, 2*m / p**2 * (p - x), 2*m / (1 - p)**2 * (p - x))

def naca4(code, n=81):                            # Selig-ordered coordinates (TE upper -> LE -> TE lower), closed TE
    m, p, t = int(code[0]) / 100, int(code[1]) / 10, int(code[2:]) / 100
    x = (1 - np.cos(np.linspace(0, np.pi, n))) / 2
    yt = 5 * t * (0.2969*np.sqrt(x) - 0.1260*x - 0.3516*x**2 + 0.2843*x**3 - 0.1036*x**4)
    yc, dyc = camber(x, m, p); th = np.arctan(dyc)
    xu, yu, xl, yl = x - yt*np.sin(th), yc + yt*np.cos(th), x + yt*np.sin(th), yc - yt*np.cos(th)
    return np.concatenate([xu[::-1], xl[1:]]), np.concatenate([yu[::-1], yl[1:]])

def thin_airfoil(m, p):                           # thin-airfoil theory: alpha_L0, ideal alpha, cm_c/4
    th = np.linspace(0, np.pi, 4001); _, dz = camber((1 - np.cos(th)) / 2, m, p)
    I = lambda f: np.trapezoid(dz * f, th)
    A1, A2 = 2 / np.pi * I(np.cos(th)), 2 / np.pi * I(np.cos(2*th))
    return -I(np.cos(th) - 1) / np.pi, I(np.ones_like(th)) / np.pi, np.pi / 4 * (A2 - A1)

def section_model(code, Re):
    """[A] Low-Re section estimate for ranking only -- verify the winner in XFOIL / wind tunnel.
    cd = cd_min + k (cl - cl_ideal)^2 ; cd_min = laminar skin friction x form factor + laminar-bubble penalty."""
    m, p, t = int(code[0]) / 100, int(code[1]) / 10, int(code[2:]) / 100
    a_L0, a_id, cm = thin_airfoil(m, p)
    cl_id = LIFT_SLOPE_FAC * 2 * np.pi * (a_id - a_L0)
    cd_min = 2 * 1.328 / np.sqrt(Re) * (1 + 2*t + 60*t**4) + 0.46 * t**2 * np.sqrt(1e5 / Re)
    k = 0.010 * 0.10 / t                          # thicker sections -> wider drag bucket
    clmax = (0.85 + 6*m + 2*(min(t, 0.12) - 0.06)) * min(1.0, (Re / 1e5)**0.1)
    return dict(clmax=clmax, cm=cm, cd=lambda cl: cd_min + k * (cl - cl_id)**2, src="model")

def section_neuralfoil(code, Re):                 # used automatically if `pip install neuralfoil` is available
    import neuralfoil as nf
    x, y = naca4(code); al = np.linspace(-4, 16, 41)
    r = nf.get_aero_from_coordinates(coordinates=np.column_stack([x, y]), alpha=al, Re=Re, model_size="large")
    cl, cd, cm = (np.asarray(r[k]).ravel() for k in ("CL", "CD", "CM"))
    i = int(np.argmax(cl)); cl, cd, cm = cl[:i + 1], cd[:i + 1], cm[:i + 1]
    j = np.argsort(cl); cl, cd, cm = cl[j], cd[j], cm[j]
    return dict(clmax=cl[-1], cm=float(np.interp(0.5, cl, cm)), cd=lambda c: np.interp(c, cl, cd), src="NeuralFoil")

def section_aero(code, Re):
    try: return section_neuralfoil(code, Re)
    except ImportError: return section_model(code, Re)

def select_airfoil(S=S_BASE, AR=AR_BASE, m=M_TARGET, V=V_CRUISE, verbose=True):
    c = np.sqrt(S / AR); Re = RHO * V * c / MU
    CL = m * g / (0.5 * RHO * V**2 * S); CL_turn = load_factor(TURN_BANK) * CL
    rows = []
    for code in CANDIDATES:
        a = section_aero(code, Re); t = int(code[2:]) / 100
        CLmax = 0.9 * a["clmax"]                  # [A] 3D/2D CLmax ratio
        LD = CL / (CD0_REST + a["cd"](CL) + K_factor(AR) * CL**2)
        ok = t >= T_MIN_PRINT and abs(a["cm"]) <= CM_MAX and CL_turn <= 0.85 * CLmax
        rows.append(dict(code=code, t=t, LD=LD, CLmax=CLmax, cm=a["cm"], Vs=stall_speed(m, S, CLmax), ok=ok, cd=a["cd"], src=a["src"]))
    feas = [r for r in rows if r["ok"]] or rows
    span = {k: (min(f(r) for r in feas), max(f(r) for r in feas)) for k, f in
            [("LD", lambda r: r["LD"]), ("CLmax", lambda r: r["CLmax"]), ("cm", lambda r: -abs(r["cm"]))]}
    nrm = lambda k, v: (v - span[k][0]) / (span[k][1] - span[k][0] + 1e-12)   # min-max over feasible set
    for r in rows:
        r["score"] = (W_SCORE["LD"] * nrm("LD", r["LD"]) + W_SCORE["CLmax"] * nrm("CLmax", r["CLmax"])
                      + W_SCORE["cm"] * nrm("cm", -abs(r["cm"]))) if r["ok"] else -1
    rows.sort(key=lambda r: -r["score"])
    if verbose:
        print(f"\nAirfoil selection ({rows[0]['src']}): Re = {Re:,.0f}, CL_cruise = {CL:.2f}, CL_turn({TURN_BANK} deg) = {CL_turn:.2f}")
        print(f"{'NACA':>6} {'t/c':>5} {'L/D_ac':>7} {'CLmax':>6} {'cm':>7} {'Vs':>5} {'score':>6}")
        for r in rows[:10]:
            print(f"{r['code']:>6} {r['t']:5.2f} {r['LD']:7.2f} {r['CLmax']:6.2f} {r['cm']:7.3f} {r['Vs']:5.2f} {r['score']:6.3f}")
        print(f"Best: NACA {rows[0]['code']}  (rejected {len(rows) - len(feas)} for t/c < {T_MIN_PRINT}, |cm| > {CM_MAX} or turn CL margin)")
    return rows, Re, CL

def fig_airfoils(rows, Re, CL, n=5):
    fig, ax = plt.subplots(1, 2, figsize=(9.0, 3.2), gridspec_kw={"width_ratios": [1.3, 1]})
    cl = np.linspace(0.0, 1.1, 200)
    for i, r in enumerate(rows[:n]):
        x, y = naca4(r["code"]); lw = 2.2 if i == 0 else 1.0
        ax[0].plot(x, y - 0.09 * i, color=COL[i], lw=lw); ax[0].text(1.02, -0.09 * i, f"NACA {r['code']}  ({r['score']:.2f})", fontsize=7, va="center")
        c = cl[cl <= r["CLmax"] / 0.9]; ax[1].plot(c, c / r["cd"](c), color=COL[i], lw=lw, label=f"NACA {r['code']}")
    ax[0].set_aspect("equal"); ax[0].set_xlim(-0.02, 1.35); ax[0].axis("off"); ax[0].set_title("Top candidates (score)", fontsize=9)
    ax[1].axvline(CL, color="#52514e", ls="--", lw=1); ax[1].text(CL, ax[1].get_ylim()[0], " cruise CL", fontsize=7, va="bottom")
    ax[1].set_xlabel("cl"); ax[1].set_ylabel("cl/cd (section)"); ax[1].set_title(f"Re = {Re:,.0f}", fontsize=9)
    ax[1].legend(fontsize=7); ax[1].grid(alpha=.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/7_airfoil_selection.png", dpi=200); plt.close()

# ======================== Top-down layout =========================
def layout(S=S_BASE, AR=AR_BASE, lam=TAPER):
    b = np.sqrt(AR * S); cr = 2 * S / (b * (1 + lam)); ct = lam * cr
    mac = 2 / 3 * cr * (1 + lam + lam**2) / (1 + lam)
    x_ac = X_LE_ROOT + 0.25 * cr                  # straight quarter-chord -> ac sits on root c/4
    Sh = V_H * S * mac / TAIL_ARM; bh = np.sqrt(AR_H * Sh); ch = Sh / bh
    Sv = V_V * S * b / TAIL_ARM; hv = np.sqrt(AR_V * Sv); cv = Sv / hv
    x_le_h = x_ac + TAIL_ARM - 0.25 * ch; x_te = x_le_h + ch
    a0 = LIFT_SLOPE_FAC * 2 * np.pi               # neutral point: h_n = h_ac + eta V_H (a_t/a_w)(1 - de/da)
    aw, at = a0 / (1 + a0 / (np.pi * E_OSW * AR)), a0 / (1 + a0 / (np.pi * E_OSW * AR_H))
    x_np = x_ac + 0.9 * V_H * (at / aw) * (1 - 2 * aw / (np.pi * AR)) * mac
    return dict(b=b, cr=cr, ct=ct, mac=mac, x_ac=x_ac, Sh=Sh, bh=bh, ch=ch, Sv=Sv, hv=hv, cv=cv,
                x_le_h=x_le_h, x_te=x_te, x_np=x_np, x_cg=x_np - STATIC_MARGIN * mac)

def fig_planform(best):
    L = layout(); mm = lambda v: np.asarray(v) * 1000
    b, cr, ct, xt = L["b"], L["cr"], L["ct"], L["x_te"]
    fig = plt.figure(figsize=(9.5, 6.4)); ax = fig.add_axes([0.04, 0.06, 0.66, 0.88])
    # fuselage (half-width profile) and prop
    xf = [0, 0.03, X_LE_ROOT, X_LE_ROOT + cr, xt]; wf = np.array([0.7, 1.0, 1.0, 1.0, 0.35]) * FUSE_W / 2
    ax.fill(mm(np.r_[wf, -wf[::-1]]), mm(np.r_[xf, xf[::-1]]), color="#d8d6d0", ec="#52514e", lw=1, zorder=3)
    ax.plot(mm([-PROP_D / 2, PROP_D / 2]), mm([-0.008] * 2), color="#52514e", lw=3, solid_capstyle="round", zorder=4)
    ax.text(mm(PROP_D / 2) + 8, mm(-0.008), "prop", fontsize=7, va="center")
    # wing (quarter-chord straight), print-panel splits
    for s in (1, -1):
        y = np.array([0, s * b / 2, s * b / 2, 0]); x = np.array([X_LE_ROOT, X_LE_ROOT + 0.25 * (cr - ct), X_LE_ROOT + 0.25 * (cr - ct) + ct, X_LE_ROOT + cr])
        ax.fill(mm(y), mm(x), color=COL[0], alpha=0.25, ec=COL[0], lw=1.5, zorder=2)
        npan = int(np.ceil(b / 2 / PRINT_BED))
        for k in range(1, npan):
            yk = k * b / 2 / npan; ck = cr + (ct - cr) * yk / (b / 2); xk = X_LE_ROOT + 0.25 * (cr - ck)
            ax.plot(mm([s * yk] * 2), mm([xk, xk + ck]), color=COL[0], ls="--", lw=1, zorder=2)
        # horizontal tail
        ax.fill(mm([0, s * L["bh"] / 2, s * L["bh"] / 2, 0]), mm([L["x_le_h"], L["x_le_h"], xt, xt]), color=COL[2], alpha=0.3, ec=COL[2], lw=1.5, zorder=2)
    ax.plot([0, 0], mm([xt - L["cv"], xt]), color=COL[1], lw=4, solid_capstyle="butt", zorder=5)
    ax.text(6, mm(xt - L["cv"] / 2), "fin", fontsize=7, color=COL[1], va="center", zorder=6)
    # CG / NP markers
    ax.plot(0, mm(L["x_cg"]), "o", ms=9, mfc="white", mec="k", zorder=6); ax.plot(0, mm(L["x_cg"]), "+", ms=9, color="k", zorder=7)
    ax.plot(0, mm(L["x_np"]), "^", ms=7, color=COL[3], mec="k", zorder=6)
    ax.text(-mm(FUSE_W / 2) - 6, mm(L["x_cg"]), "CG", fontsize=7, ha="right", va="center")
    ax.text(mm(FUSE_W / 2) + 6, mm(L["x_np"]), "NP", fontsize=7, va="center")
    # dimensions
    dim = lambda p0, p1, txt, off=(0, 0), **kw: (ax.annotate("", p0, p1, arrowprops=dict(arrowstyle="<->", lw=0.8, color="#52514e")),
                                                ax.text((p0[0] + p1[0]) / 2 + off[0], (p0[1] + p1[1]) / 2 + off[1], txt, fontsize=7, **{"ha": "center", **kw}))
    yb = mm(xt) + 35; dim((-mm(b / 2), yb), (mm(b / 2), yb), f"span b = {mm(b):.0f} mm", (0, 12))
    yt_ = mm(b / 2) + 18; xlt = X_LE_ROOT + 0.25 * (cr - ct); dim((yt_, mm(xlt)), (yt_, mm(xlt + ct)), f"ct {mm(ct):.0f}", (16, 0), va="center")
    cq = (cr + ct) / 2; xq = X_LE_ROOT + 0.25 * (cr - cq)          # chord at quarter span
    dim((-mm(b / 4), mm(xq)), (-mm(b / 4), mm(xq + cq)), f"c {mm(cq):.0f}", (-6, 0), ha="right", va="center")
    yh = mm(L["bh"] / 2) + 15; dim((yh, mm(L["x_ac"])), (yh, mm(L["x_ac"] + TAIL_ARM)), f"l_t {mm(TAIL_ARM):.0f}", (6, 0), ha="left", va="center")
    yl = -mm(L["bh"] / 2) - 15; dim((yl, 0), (yl, mm(xt)), f"L {mm(xt):.0f}", (-6, 0), ha="right", va="center")
    ax.set_aspect("equal"); ax.invert_yaxis(); ax.set_xlabel("y, spanwise (mm)"); ax.set_ylabel("x from motor face (mm)")
    ax.set_title(f"Top-down layout — NACA {best['code']}, S = {S_BASE} m², AR = {AR_BASE}, λ = {TAPER}", fontsize=10)
    ax.grid(alpha=.2); ax.set_ylim(yb + 30, -45); ax.set_xlim(-mm(b / 2) - 40, mm(b / 2) + 75)
    # summary panel + airfoil inset
    m_est, _ = mass_from_span(b, WALLS_MM[-1])
    info = [("Span b", f"{mm(b):.0f} mm"), ("Root / tip chord", f"{mm(cr):.0f} / {mm(ct):.0f} mm"), ("MAC", f"{mm(L['mac']):.0f} mm"),
            ("Wing area S", f"{S_BASE*1e4:.0f} cm²"), ("Airfoil", f"NACA {best['code']}"), ("CLmax (3D est.)", f"{best['CLmax']:.2f}"),
            ("Vs @ target mass", f"{best['Vs']:.2f} m/s"), ("W/S", f"{M_TARGET*g/S_BASE:.1f} N/m²"),
            ("Mass est. (Lab 1, %.1f mm)" % WALLS_MM[-1], f"{m_est:.0f} g"), ("H-tail", f"{mm(L['bh']):.0f} x {mm(L['ch']):.0f} mm (V_H {V_H})"),
            ("Fin", f"{mm(L['hv']):.0f} h x {mm(L['cv']):.0f} mm (V_V {V_V})"), ("Tail arm l_t", f"{mm(TAIL_ARM):.0f} mm"),
            ("NP / CG from LE root", f"{mm(L['x_np'] - X_LE_ROOT):.0f} / {mm(L['x_cg'] - X_LE_ROOT):.0f} mm"), ("Static margin", f"{STATIC_MARGIN*100:.0f}% MAC"),
            ("Wing panels / side", f"{int(np.ceil(b / 2 / PRINT_BED))} (bed {mm(PRINT_BED):.0f} mm)")]
    for i, (k, v) in enumerate(info):
        fig.text(0.72, 0.90 - i * 0.04, k, fontsize=8, color="#52514e"); fig.text(0.985, 0.90 - i * 0.04, v, fontsize=8, ha="right")
    fig.text(0.72, 0.93, "Design summary (replace [A]/[I] with [M])", fontsize=8, weight="bold")
    ai = fig.add_axes([0.72, 0.06, 0.26, 0.14]); x, y = naca4(best["code"])
    ai.fill(x * mm(cr), y * mm(cr), color=COL[0], alpha=0.3, ec=COL[0]); ai.set_aspect("equal"); ai.set_title(f"Root section, NACA {best['code']} ({mm(cr):.0f} mm)", fontsize=7)
    ai.tick_params(labelsize=6); ai.grid(alpha=.2)
    fig.savefig(f"{OUT}/8_planform_top_view.png", dpi=200); plt.close()
    if m_est > 249.9: print(f"WARNING: Lab 1 mass scaling gives {m_est:.0f} g at b = {b:.3f} m (> 249.9 g)")

if __name__ == "__main__":
    vs = stall_speed(M_TARGET, S_BASE, CLMAX)
    print(f"Baseline Vs = {vs:.2f} m/s, launch >= {K_LAUNCH*vs:.2f} m/s, W/S = {M_TARGET*g/S_BASE:.1f} N/m^2")
    fig_stall(); fig_turn(); fig_turn_stall(); fig_thrust(); fig_ld(); fig_span()
    rows, Re, CL = select_airfoil(); fig_airfoils(rows, Re, CL); fig_planform(rows[0])
    print(f"Figures written to ./{OUT}")