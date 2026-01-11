import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# Grid and simulation params
# ----------------------------
Nx, Ny = 1000, 1000
dx = dy = 1.0
dt = 0.3
n_steps = 4000

# ----------------------------
# Material tensors: rho(x,y), K(x,y)
# ----------------------------
rho = np.ones((Nx, Ny))
K   = np.ones((Nx, Ny))

xg, yg = np.meshgrid(np.arange(Nx), np.arange(Ny), indexing="ij")
mask = (xg - (9/10)*Nx)**2 + (yg - Ny/2)**2 < 40**2
rho[mask] = 8

# ----------------------------
# Wavefield arrays
# ----------------------------
u_prev = np.zeros((Nx, Ny))   # u at time n-1
u      = np.zeros((Nx, Ny))   # u at time n

# Initial condition: Gaussian bump
cx, cy = Nx // 3, Ny // 2
u0 = 100*np.exp(-(((xg - cx)**2 + (yg - cy)**2) / (2 * 10.0**2)))
u[:] = u0
u_prev[:] = u0

# ----------------------------
# Absorbing boundary (sponge layer)
# ----------------------------

# ----------------------------
# Absorbing boundary (sponge layer)
# ----------------------------
b_depth = 200  # thickness in cells

c0 = float(np.sqrt(np.median(K / rho)))  # representative wavespeed for tuning

R = 1e-5
m = 2
L = b_depth * dx
sigma_max = -(c0 * (m + 1) / L) * np.log(R)

# Build sigma(x,y)
ii = np.arange(Nx)[:, None]         # (Nx,1)
jj = np.arange(Ny)[None, :]         # (1,Ny)

# distances to each edge, all broadcast to (Nx,Ny)
d_left   = ii
d_right  = (Nx - 1) - ii
d_bottom = jj
d_top    = (Ny - 1) - jj

# distance to nearest boundary, shape (Nx,Ny)
dist_to_edge = np.minimum(np.minimum(d_left, d_right), np.minimum(d_bottom, d_top)).astype(float)

sigma = np.zeros((Nx, Ny), dtype=float)
in_sponge = dist_to_edge < b_depth

# normalized depth into sponge: t=0 at interior edge, t=1 at boundary
t = (b_depth - dist_to_edge[in_sponge]) / b_depth

# polynomial ramp
sigma[in_sponge] = sigma_max * (t ** m)

sig_dt = sigma * dt
denom = 1.0 + sig_dt
coef_prev = 1.0 - sig_dt
sigma[in_sponge] = sigma_max * (t ** m)

# Precompute factors used by the damped update
# (avoid recomputing every time step)
sig_dt = sigma * dt
denom  = 1.0 + sig_dt
coef_prev = 1.0 - sig_dt  # used as (1 - sigma*dt)

# ----------------------------
# Time stepping loop
# ----------------------------
plt.ion()
fig, ax = plt.subplots()

for n in range(n_steps):
    # Face-averaged K in x and y directions
    Kx_plus  = np.zeros_like(K)
    Kx_minus = np.zeros_like(K)
    Ky_plus  = np.zeros_like(K)
    Ky_minus = np.zeros_like(K)

    Kx_plus[:-1, :] = 0.5 * (K[:-1, :] + K[1:, :])
    Kx_minus[1:, :] = Kx_plus[:-1, :]

    Ky_plus[:, :-1] = 0.5 * (K[:, :-1] + K[:, 1:])
    Ky_minus[:, 1:] = Ky_plus[:, :-1]

    # Compute dx(K ux)
    Fx = np.zeros_like(u)
    Fx[:-1, :] += Kx_plus[:-1, :] * (u[1:, :] - u[:-1, :])
    Fx[1:, :]  -= Kx_minus[1:, :] * (u[1:, :] - u[:-1, :])
    Fx /= dx**2

    # Compute dy(K uy)
    Fy = np.zeros_like(u)
    Fy[:, :-1] += Ky_plus[:, :-1] * (u[:, 1:] - u[:, :-1])
    Fy[:, 1:]  -= Ky_minus[:, 1:] * (u[:, 1:] - u[:, :-1])
    Fy /= dy**2

    L_op = Fx + Fy

    # ----------------------------
    # Damped time update (absorbing boundaries)
    # u_tt + 2*sigma*u_t = L/rho
    # Discretization:
    # u_next = [2u - (1 - sigma*dt)u_prev + dt^2*(L/rho)] / (1 + sigma*dt)
    # ----------------------------
    accel = L_op / rho
    u_next = (2.0*u - coef_prev*u_prev + (dt**2)*accel) / denom

    # Rotate time levels
    u_prev, u = u, u_next

    # Visualization
    if n % 10 == 0:
        ax.clear()
        im = ax.imshow(u.T, origin="lower", cmap="viridis", vmin=-1, vmax=1)
        ax.set_title(f"Step {n}  (sponge depth={b_depth}, sigma_max={sigma_max:.3g})")
        plt.pause(0.05)

plt.ioff()
plt.show()
