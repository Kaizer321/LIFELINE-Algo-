import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from itertools import permutations, combinations
from config import SEED, tier_of, scenario_of
from traps import _route_stats, greedy_value, knapsack

# ---------------------------------------------------------------- capacity
def choose_capacity(rng, crates, tier, fixed):
    cr = [(r[1], r[3], r[4]) for r in crates]            # (id, weight, value)
    total = sum(w for _, w, _ in cr)
    if fixed is not None:
        return fixed, greedy_value(cr, fixed) < knapsack(cr, fixed)
    lo = max(1, -(-total // 10))                          # ceil(10%)
    hi = (7 * total) // 10                                # floor(70%)
    if tier == "S":
        failing = [c for c in range(lo, hi + 1)
                   if greedy_value(cr, c) < knapsack(cr, c)]
        if failing:
            return rng.choice(failing), True
    cap = rng.randint(lo, hi)
    return cap, greedy_value(cr, cap) < knapsack(cr, cap)

# ---------------------------------------------------------------- targets
def build_adj(locs, roads):
    pen = [r[3] for r in locs]
    adj = [[] for _ in locs]
    for _, _, u, v, m, _ in roads:
        adj[u].append((v, m + pen[v]))
        adj[v].append((u, m + pen[u]))
    return adj

def adjust_targets(rng, locs, roads, targets):
    """Make sure at least one target shows 'fewest roads costs more than cheapest'."""
    V = len(locs)
    adj = build_adj(locs, roads)

    def trapped(t):
        fc, d, _, _ = _route_stats(V, adj, t)
        return fc > d

    if any(trapped(t) for t in targets):
        return targets, True
    cands = [t for t in range(1, V)
             if locs[t][2] in ("S", "H") and t not in targets[:2] and trapped(t)]
    if cands:
        targets = targets[:2] + [rng.choice(cands)]
        return targets, True
    return targets, False

# ---------------------------------------------------------------- claims
def cargo_exhaustive(cr, cap):
    best = 0

    def dfs(i, left, val):
        nonlocal best
        best = max(best, val)
        for j in range(i, len(cr)):
            if cr[j][1] <= left:
                dfs(j + 1, left - cr[j][1], val + cr[j][2])
    dfs(0, cap, 0)
    return best

def windows_exhaustive(ws):
    ws = sorted(ws)                                       # (start, finish, value)
    best = [0, 0]

    def dfs(i, last, c, v):
        best[0], best[1] = max(best[0], c), max(best[1], v)
        for j in range(i, len(ws)):
            if ws[j][0] >= last:                          # touching is compatible
                dfs(j + 1, ws[j][1], c + 1, v + ws[j][2])
    dfs(0, 0, 0, 0)
    return best[0], best[1]

def drum_exhaustive(prices, L):
    def f(n):
        return 0 if n == 0 else max(prices[j - 1] + f(n - j) for j in range(1, n + 1))
    return f(L)

def tour_exhaustive(pts):
    n = len(pts)
    d = [[abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in pts] for a in pts]
    best = None
    for perm in permutations(range(1, n)):
        t = d[0][perm[0]] + d[perm[-1]][0]
        t += sum(d[perm[i]][perm[i + 1]] for i in range(n - 2))
        if best is None or t < best:
            best = t
    return best

def cover_exhaustive(N, edges):
    masks = [(1 << u) | (1 << v) for u, v in edges]
    for k in range(N + 1):
        for comb in combinations(range(N), k):
            s = sum(1 << c for c in comb)
            if all(m & s for m in masks):
                return k

def make_claims(cid, cap, t, info):
    cr = [(r[1], r[3], r[4]) for r in t["crates"]]
    ws = [(r[2], r[3], r[4]) for r in t["windows"]]
    prices = [r[2] for r in t["drum_prices"]]
    pts = [(r[2], r[3]) for r in t["sites"]]
    N = info["sensor_nodes"]
    edges = [(r[1], r[2]) for r in t["sensor_edges"]]

    cargo = cargo_exhaustive(cr, cap)
    wc, wv = windows_exhaustive(ws)
    drum = drum_exhaustive(prices, len(prices))
    tour = tour_exhaustive(pts)
    cover = cover_exhaustive(N, edges)

    # ---- cross-checks with independent methods ----
    assert cargo == knapsack(cr, cap), "cargo: exhaustive vs DP"
    last, cnt = 0, 0
    for s, f, _ in sorted(ws, key=lambda w: (w[1], w[0])):    # earliest finish first
        if s >= last:
            cnt, last = cnt + 1, f
    assert cnt == wc, "window count: exhaustive vs earliest-finish"
    best = [0] * (len(prices) + 1)
    for n in range(1, len(prices) + 1):
        best[n] = max(prices[j - 1] + best[n - j] for j in range(1, n + 1))
    assert best[-1] == drum, "drum: exhaustive vs DP"
    assert tour <= info["tour_length"], "optimal tour longer than planted tour"
    assert cover <= info["sensor_k"], "min cover larger than planted cover"
    return [cid, cargo, wc, wv, drum, tour, cover]

# ---------------------------------------------------------------- main entry
def finalize_case(k, rng, cid, t, info):
    tier = tier_of(k)
    cap, greedy_fail = choose_capacity(rng, t["crates"], tier, info.get("capacity"))
    targets, route_trap = info["targets"], False
    if tier == "S":
        targets, route_trap = adjust_targets(rng, t["locations"], t["roads"], targets)

    total = sum(r[3] for r in t["crates"])
    assert 1 <= cap and (k == 47 or 0.1 * total <= cap <= 0.7 * total)
    assert len(set(targets)) == 3 and 0 not in targets

    row = [cid, SEED, k, tier, scenario_of(k), cap, targets[0], targets[1], targets[2],
           info["edit_bound"], info["tour_length"], info["sensor_nodes"],
           info["sensor_k"], info["safety_vars"], info["rations_target"]]
    claims = make_claims(cid, cap, t, info) if tier == "S" else None
    return row, claims, {"greedy_fail": greedy_fail, "route_trap": route_trap}