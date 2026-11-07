"""Outcome models Y_i(z) = base_i + m_i(z) + eps_i with fixed unit baselines.

Randomness over repetitions comes from the assignment z (and fresh measurement noise eps).
`signal(z)` returns m_i(z); GATE = mean(signal(1) - signal(0)).
Exposure summaries: f = W z (neighbour treated fraction), f2 = W^2 z (2-hop walk fraction),
c = A z (neighbour treated count).
"""
import numpy as np
from dataclasses import dataclass


@dataclass
class Outcome:
    kind: str = "lin_frac"
    tau: float = 1.0          # direct effect
    gamma: float = 1.0        # interference (spillover) strength at full neighbour exposure
    gamma2: float = 0.0       # 2-hop strength (kind lin_2hop)
    q: float = 1.0            # curvature: g(f) = f**q  (kind 'pow')
    steep: float = 10.0       # steepness of the threshold (kind 'thresh')
    thr: float = 0.5          # threshold location
    het: float = 0.0          # heterogeneity: gamma_i = gamma * (1 + het * zdeg_i)
    sigma_a: float = 1.0      # SD of fixed baseline
    sigma_c: float = 1.0      # SD of community-level baseline component
    rho_deg: float = 0.5      # baseline correlation with log-degree
    sigma_e: float = 1.0      # SD of fresh measurement noise

    def setup(self, net, comm, rng):
        n = net.n
        ld = np.log(net.deg)
        zd = (ld - ld.mean()) / (ld.std() + 1e-12)
        self.zdeg = zd
        k = comm.max() + 1
        ce = rng.normal(size=k)[comm]
        self.base = self.sigma_a * (self.rho_deg * zd + np.sqrt(1 - self.rho_deg**2) * rng.normal(size=n)) \
            + self.sigma_c * ce
        self.net = net
        return self

    def exposure_g(self, f):
        k = self.kind
        if k in ("lin_frac", "lin_2hop", "lin_count"):
            return f
        if k == "pow":
            return f ** self.q
        if k == "sat":      # concave saturation g(f) = (1-exp(-kappa f))/(1-exp(-kappa)), kappa = self.steep
            return (1 - np.exp(-self.steep * f)) / (1 - np.exp(-self.steep))
        if k == "thresh":   # logistic in neighbour fraction, scaled to [0,1]
            s = lambda x: 1 / (1 + np.exp(-self.steep * (x - self.thr)))
            return (s(f) - s(0.0)) / (s(1.0) - s(0.0))
        raise ValueError(k)

    def signal(self, z):
        net = self.net
        f = net.W @ z
        gam = self.gamma * (1 + self.het * self.zdeg)
        if self.kind == "lin_count":     # spillover grows with the *number* of treated neighbours
            c = net.A @ z
            return self.tau * z + self.gamma * c / net.deg.mean()
        m = self.tau * z + gam * self.exposure_g(f)
        if self.kind == "lin_2hop":
            m = m + self.gamma2 * (net.W @ f)
        return m

    def gate(self):
        n = self.net.n
        return float(np.mean(self.signal(np.ones(n)) - self.signal(np.zeros(n))))

    def observe(self, z, rng):
        return self.base + self.signal(z) + self.sigma_e * rng.normal(size=self.net.n)
