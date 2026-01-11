import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# Grid and simulation params
# ----------------------------
Nx, Ny = 400, 400     # grid size
dx = dy = 1.0           # spatial step
dt = 0.3                # time step (keep small for stability)
n_steps = 1600          # number of time steps

# ----------------------------
# Material tensors: rho(x,y), K(x,y)
# ----------------------------
rho = np.ones((Nx, Ny))      # density field
K   = np.ones((Nx, Ny))      # stiffness / bulk modulus field

# Example: circular region in the center with different properties
xg, yg = np.meshgrid(np.arange(Nx), np.arange(Ny), indexing="ij")
mask = (xg - Nx/2)**2 + (yg - Ny/2)**2 < 40**2

#K[mask]   = 2.0   # stiffer blob
rho[mask] = 4.5   # denser blob

# ----------------------------
# Wavefield arrays
# ----------------------------
u_prev = np.zeros((Nx, Ny))   # u at time n-1
u      = np.zeros((Nx, Ny))   # u at time n

# Initial condition: Gaussian bump
cx, cy = Nx // 3, Ny // 2
u0 = np.exp(-(((xg - cx)**2 + (yg - cy)**2) / (2 * 10.0**2)))
u[:] = u0
u_prev[:] = u0

# ----------------------------
# Time stepping loop
# ----------------------------
plt.ion()
fig, ax = plt.subplots()

# -----------------------------
# Boundary 
# -----------------------------
b_depth = 20
acoustic_imp_rmp = np.arange(1, b_depth+1)**2

for n in range(n_steps):
    # Face-averaged K (stiffness) in x and y directions
    Kx_plus  = np.zeros_like(K)
    Kx_minus = np.zeros_like(K)
    Ky_plus  = np.zeros_like(K)
    Ky_minus = np.zeros_like(K)

    # x-direction averages: between (i,j) and (i+1,j)
    Kx_plus[:-1, :] = 0.5 * (K[:-1, :] + K[1:, :])
    Kx_minus[1:, :] = Kx_plus[:-1, :]

    # y-direction averages: between (i,j) and (i,j+1)
    Ky_plus[:, :-1] = 0.5 * (K[:, :-1] + K[:, 1:])
    Ky_minus[:, 1:] = Ky_plus[:, :-1]

    Fx = np.zeros_like(u)
    # right face flux
    Fx[:-1, :] += Kx_plus[:-1, :] * (u[1:, :] - u[:-1, :])
    # left face flux
    Fx[1:, :]  -= Kx_minus[1:, :] * (u[1:, :] - u[:-1, :])
    Fx /= dx**2

    # Compute dy(K uy)
    Fy = np.zeros_like(u)
    # top face flux
    Fy[:, :-1] += Ky_plus[:, :-1] * (u[:, 1:] - u[:, :-1])
    # bottom face flux
    Fy[:, 1:]  -= Ky_minus[:, 1:] * (u[:, 1:] - u[:, :-1])
    Fy /= dy**2

    # Total "force" term L = dx(K ux) + dy(K uy)
    L = Fx + Fy

    # Time update:  rho * u_tt = L   u_tt = L / rho
    u_next = 2*u - u_prev + dt**2 * (L / rho)

    # # Simple fixed boundary conditions
    # u_next[0, :]   = 0
    # u_next[-1, :]  = 0
    # u_next[:, 0]   = 0
    # u_next[:, -1]  = 0

    # Rotate time levels
    u_prev, u = u, u_next

    # Quick visualization every few steps
    if n % 10 == 0:
        ax.clear()
        #im = ax.imshow(u.T, origin="lower", cmap="RdBu", vmin=-1, vmax=1)
        im = ax.imshow(u.T, origin="lower", cmap="viridis", vmin=-1, vmax=1)
        # im = ax.imshow(u.T, origin="lower", cmap="inferno", vmin=-1, vmax=1)
        # im = ax.imshow(u.T, origin="lower", cmap="plasma", vmin=-1, vmax=1)
        # im = ax.imshow(u.T, origin="lower", cmap="magma", vmin=-1, vmax=1)                                
        # ax.set_title(f"Step")
        
        #ax.set_title(f"Step")
        plt.pause(0.05)

plt.ioff()
plt.show()
