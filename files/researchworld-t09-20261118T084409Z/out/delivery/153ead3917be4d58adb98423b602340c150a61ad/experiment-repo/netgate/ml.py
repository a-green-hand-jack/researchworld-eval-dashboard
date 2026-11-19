"""Learned regressors (REG-ML): gradient boosting / random forest on (z, g1, g2, degree) and a 2-layer GCN on z."""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor


def _X(ctx, st):
    return np.column_stack([st["z"], st["g1"], st["g2"], np.log(ctx.deg)])


def gbm(ctx, spec, st, y, seed=0):
    m = HistGradientBoostingRegressor(max_iter=150, learning_rate=0.1, max_depth=3, random_state=seed)
    m.fit(_X(ctx, st), y)
    return float(np.mean(m.predict(_X(ctx, ctx.corner(1))) - m.predict(_X(ctx, ctx.corner(0)))))


def rf(ctx, spec, st, y, seed=0):
    m = RandomForestRegressor(n_estimators=100, min_samples_leaf=10, n_jobs=1, random_state=seed)
    m.fit(_X(ctx, st), y)
    return float(np.mean(m.predict(_X(ctx, ctx.corner(1))) - m.predict(_X(ctx, ctx.corner(0)))))


def gcn(ctx, spec, st, y, seed=0, hidden=16, epochs=200, layers=2):
    import torch
    import scipy.sparse as sp
    torch.manual_seed(seed)
    n = ctx.n
    A = ctx.A + sp.identity(n, format="csr")
    dinv = 1 / np.sqrt(np.asarray(A.sum(1)).ravel())
    An = sp.diags(dinv) @ A @ sp.diags(dinv)
    An = An.tocoo()
    idx = torch.tensor(np.vstack([An.row, An.col]), dtype=torch.long)
    Ahat = torch.sparse_coo_tensor(idx, torch.tensor(An.data, dtype=torch.float32), (n, n)).coalesce()
    ld = np.log(ctx.deg); ld = (ld - ld.mean()) / (ld.std() + 1e-9)
    ldt = torch.tensor(ld, dtype=torch.float32)[:, None]

    class Net(torch.nn.Module):
        def __init__(s):
            super().__init__()
            s.l1 = torch.nn.Linear(2, hidden)
            s.l2 = torch.nn.Linear(hidden, hidden)
            s.lo = torch.nn.Linear(hidden, 1)
            s.dir = torch.nn.Linear(1, 1)  # direct term on own z

        def forward(s, z):
            h = torch.relu(torch.sparse.mm(Ahat, s.l1(torch.cat([z[:, None], ldt], 1))))
            if layers > 1:
                h = torch.relu(torch.sparse.mm(Ahat, s.l2(h)))
            return (s.lo(h) + s.dir(z[:, None])).squeeze(1)

    net = Net()
    opt = torch.optim.Adam(net.parameters(), lr=0.02, weight_decay=1e-4)
    zt = torch.tensor(st["z"], dtype=torch.float32)
    mu, sd = y.mean(), y.std() + 1e-9
    yt = torch.tensor((y - mu) / sd, dtype=torch.float32)
    for _ in range(epochs):
        opt.zero_grad()
        loss = torch.mean((net(zt) - yt) ** 2)
        loss.backward()
        opt.step()
    with torch.no_grad():
        o = torch.ones(n); zr = torch.zeros(n)
        return float((net(o) - net(zr)).mean() * sd)


def ml_estimates(ctx, spec, st, y, which):
    out = {}
    for w in which:
        out["REG-" + w.upper()] = dict(gbm=gbm, rf=rf, gcn=gcn)[w](ctx, spec, st, y)
    return out
