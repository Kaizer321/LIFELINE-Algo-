import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collections import deque
from config import RANGES, tier_of, scenario_of, PENALTIES

# allowed average degree (inclusive) per case study
DEG = {1: (2.2, 3.2), 2: (2.0, 2.6), 3: (2.2, 3.0),
       4: (3.5, 5.0), 5: (2.0, 2.4), 6: (2.2, 3.0)}

def _adj(V, edges, skip=frozenset()):
    adj = [[] for _ in range(V)]
    for i, (u, v) in enumerate(edges):
        if i in skip:
            continue
        adj[u].append(v)
        adj[v].append(u)
    return adj

def _bfs(V, adj, s=0):
    d = [-1] * V
    d[s] = 0
    q = deque([s])
    while q:
        x = q.popleft()
        for y in adj[x]:
            if d[y] < 0:
                d[y] = d[x] + 1
                q.append(y)
    return d

def _pick_edge_count(rng, V, sc):
    lo, hi = DEG[sc]
    e_min = max(V - 1, math.ceil(lo * V / 2))
    e_max = min(3 * V, V * (V - 1) // 2, math.floor(hi * V / 2))
    return rng.randint(e_min, e_max)

def _generic_edges(rng, V, E):
    edges = set()
    for i in range(1, V):                       # random tree => connected
        edges.add((rng.randrange(i), i))
    while len(edges) < E:
        u, v = rng.sample(range(V), 2)
        edges.add((min(u, v), max(u, v)))
    return list(edges)

def _landslide_edges(rng, V, E):
    """Path 0..V-1 plus short chords that never cross the bridge (b, b+1)."""
    edges = {(i, i + 1) for i in range(V - 1)}
    deg = [0] * V
    for i in range(V - 1):
        deg[i] += 1
        deg[i + 1] += 1
    b = rng.randint(V // 2, V - 3)
    tries = 0
    while len(edges) < E and tries < 50 * V:
        tries += 1
        u = rng.randrange(V - 2)
        v = u + rng.randint(2, 3)
        if v >= V or (u <= b) != (v <= b):      # would cross the bridge
            continue
        if (u, v) in edges or deg[u] >= 4 or deg[v] >= 4:
            continue
        edges.add((u, v))
        deg[u] += 1
        deg[v] += 1
    return list(edges), b

def _make_locations(rng, V, sc):
    ids = list(range(1, V))
    rng.shuffle(ids)
    if sc == 5:                                  # V-1 must be a shelter (target_0)
        ids.remove(V - 1)
        ids.insert(0, V - 1)
    n_s = max(2, math.ceil(0.28 * V) + 1)        # > 25% shelters
    n_h = max(1, round(0.1 * V))
    types = {0: "D"}
    for j, i in enumerate(ids):
        types[i] = "S" if j < n_s else "H" if j < n_s + n_h else "J"

    pen = {0: 0}
    if sc == 1:                                  # > 40% with penalty >= 2
        heavy = set(rng.sample(range(1, V), math.ceil(0.4 * V) + 1))
        for i in range(1, V):
            pen[i] = rng.choice([2, 4, 6]) if i in heavy else rng.choice([0, 1])
    else:
        for i in range(1, V):
            pen[i] = rng.choice(PENALTIES)
    return types, pen

def _make_waves(rng, E, w, must_first=None):
    order = list(range(E))
    rng.shuffle(order)
    if must_first is not None:                   # this road lands in wave 0
        order.remove(must_first)
        order.insert(0, must_first)
    cap = max(1, E // 4)
    pos, waves = 0, []
    for i in range(w):
        remaining = E - pos - (w - i - 1)
        size = rng.randint(1, max(1, min(cap, remaining)))
        waves.append(order[pos:pos + size])
        pos += size
    return waves

def gen_network(k, rng, cid):
    tier = tier_of(k)
    if tier == "X":
        raise NotImplementedError("trap cases 46-49 handled separately")
    sc = scenario_of(k)
    lo, hi = RANGES["locations"][tier]
    V = rng.randint(lo, hi)
    E = _pick_edge_count(rng, V, sc)

    bridge = None
    if sc == 5:
        edges, b = _landslide_edges(rng, V, E)
        bridge = (b, b + 1)
    else:
        edges = _generic_edges(rng, V, E)
    rng.shuffle(edges)
    E = len(edges)

    types, pen = _make_locations(rng, V, sc)

    # targets: distinct shelters/hospitals, never the HQ
    sh = [i for i in range(1, V) if types[i] in ("S", "H")]
    if sc == 5:
        rest = [i for i in sh if i != V - 1]
        targets = [V - 1] + rng.sample(rest, 2)
    else:
        targets = rng.sample(sh, 3)

    w = rng.randint(3, 5) if sc in (1, 3, 5) else rng.randint(2, 5)
    must = edges.index(bridge) if bridge else None
    waves = _make_waves(rng, E, w, must)

    # ---- self-check (the validator will recheck independently) ----
    adj = _adj(V, edges)
    assert min(_bfs(V, adj)) >= 0, "network not connected"
    avg = 2 * E / V
    assert DEG[sc][0] <= avg <= DEG[sc][1], f"avg degree {avg}"
    if sc == 5:
        assert max(len(a) for a in adj) <= 4
        assert max(_bfs(V, adj)) >= V // 4
        blocked = {r for wv in waves for r in wv}
        d = _bfs(V, _adj(V, edges, blocked))
        assert any(d[t] < 0 for t in targets), "no target cut off"

    loc_rows = [[cid, i, types[i], pen[i]] for i in range(V)]
    road_rows = [[cid, r, u, v, rng.randint(1, 60), rng.randint(1, 100)]
                 for r, (u, v) in enumerate(edges)]
    wave_rows = [[cid, wi, r] for wi, wv in enumerate(waves) for r in sorted(wv)]
    return {"locations": loc_rows, "roads": road_rows,
            "waves": wave_rows, "targets": targets, "V": V, "E": E}