import sys, os, heapq
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from fractions import Fraction
from collections import deque
from config import ALPHABET, PENALTIES
from network import _make_waves
from radio import count_occ, make_reports, edit_distance

def _serials(rng, n):
    s = set()
    while len(s) < n:
        s.add(rng.randint(10_000_000, 99_999_999))
    return list(s)

# ---------------------------------------------------------------- case 46
def trap_crates_46(rng, cid):
    n = rng.randint(1500, 3000)
    value = sorted(rng.randint(10, 100) for _ in range(n))
    weight = sorted((rng.randint(1, 20) for _ in range(n)), reverse=True)
    expiry = sorted(rng.randint(0, 999) for _ in range(n))
    serial = sorted(_serials(rng, n))
    rows = [[cid, i + 1, rng.randint(0, 4), weight[i], value[i], expiry[i], serial[i]]
            for i in range(n)]

    def mono(xs):
        return (all(a <= b for a, b in zip(xs, xs[1:]))
                or all(a >= b for a, b in zip(xs, xs[1:])))
    ratio = [Fraction(v, w) for v, w in zip(value, weight)]
    flags = [mono(value), mono(weight), mono(expiry), mono(serial), mono(ratio)]
    assert sum(flags) >= 3, flags
    return rows

# ---------------------------------------------------------------- case 47
def greedy_value(crates, cap):
    order = sorted(crates, key=lambda c: (-Fraction(c[2], c[1]), c[0]))
    left, tot = cap, 0
    for _, w, v in order:
        if w <= left:
            left -= w
            tot += v
    return tot

def knapsack(crates, cap):
    best = [0] * (cap + 1)
    for _, w, v in crates:
        for c in range(cap, w - 1, -1):
            best[c] = max(best[c], best[c - w] + v)
    return best[cap]

def trap_crates_47(rng, cid):
    """Lure (w=1, best ratio) + pair (w=10 each). Capacity 20.
    Greedy takes lure + one of the pair (left=9, nothing fits). Optimum is the pair."""
    n = rng.randint(12, 16)
    v = rng.randint(90, 100)
    items = [(1, v // 10 + 1), (10, v), (10, v)]
    for _ in range(n - 3):                        # fillers: never fit after greedy, low ratio
        items.append((rng.randint(10, 12), rng.randint(10, 60)))
    rng.shuffle(items)
    cap = 20
    ser = _serials(rng, n)
    rows = [[cid, i + 1, rng.randint(0, 4), w, val, rng.randint(0, 999), ser[i]]
            for i, (w, val) in enumerate(items)]
    crates = [(i + 1, w, val) for i, (w, val) in enumerate(items)]

    total = sum(w for _, w, _ in crates)
    g, opt = greedy_value(crates, cap), knapsack(crates, cap)
    assert g <= 0.6 * opt, (g, opt)
    assert 0.1 * total <= cap <= 0.7 * total, (cap, total)
    assert 12 <= n <= 60
    return rows, cap

# ---------------------------------------------------------------- case 48
def _route_stats(V, adj, target):
    """(cheapest cost among fewest-roads routes, cheapest cost overall, max hops from 0)"""
    INF = float("inf")
    hop = [-1] * V
    hop[0] = 0
    order, q = [0], deque([0])
    while q:
        x = q.popleft()
        for y, _ in adj[x]:
            if hop[y] < 0:
                hop[y] = hop[x] + 1
                q.append(y)
                order.append(y)
    fc = [INF] * V
    fc[0] = 0
    for x in order:
        for y, w in adj[x]:
            if hop[y] == hop[x] + 1 and fc[x] + w < fc[y]:
                fc[y] = fc[x] + w
    dist = [INF] * V
    dist[0] = 0
    h = [(0, 0)]
    while h:
        d, x = heapq.heappop(h)
        if d > dist[x]:
            continue
        for y, w in adj[x]:
            if d + w < dist[y]:
                dist[y] = d + w
                heapq.heappush(h, (dist[y], y))
    return fc[target], dist[target], max(hop), min(hop)

def trap_network_48(rng, cid):
    V = rng.randint(1500, 3000)
    nxt = [1]
    pen, typ, edges, nbrs = {0: 0}, {0: "D"}, {}, {0: []}

    def new():
        x = nxt[0]
        nxt[0] += 1
        nbrs[x] = []
        return x

    def add(a, b, m):
        edges[(min(a, b), max(a, b))] = m
        nbrs[a].append(b)
        nbrs[b].append(a)

    # one trap gadget per target: a short expensive route, a long cheap one
    targets = []
    for t in range(3):
        g, T = new(), new()
        pen[g], typ[g] = 6, "J"
        pen[T], typ[T] = rng.choice([4, 6]), ["S", "S", "H"][t]
        add(0, g, rng.randint(55, 60))
        add(g, T, rng.randint(55, 60))
        prev = 0
        for _ in range(rng.randint(4, 8)):
            c = new()
            pen[c], typ[c] = 0, "J"
            add(prev, c, rng.randint(1, 4))
            prev = c
        add(prev, T, rng.randint(1, 4))
        targets.append(T)

    # long tail path from the HQ: gives distance >= 500 roads
    path = [0]
    for _ in range(rng.randint(900, 1000)):
        p = new()
        pen[p], typ[p] = rng.choice(PENALTIES), rng.choice("SHJJ")
        add(path[-1], p, rng.randint(1, 60))
        path.append(p)

    # remaining locations hang off the path as bushes
    pool, bush = list(path), []
    while nxt[0] < V:
        x = new()
        pen[x], typ[x] = rng.choice(PENALTIES), rng.choice("SHJJJ")
        add(rng.choice(pool), x, rng.randint(1, 60))
        pool.append(x)
        bush.append(x)

    # extra roads only inside one bush, so the path distance is never shortened
    bush_set = set(bush)
    extra = rng.randint(V // 10, V // 4)
    done, tries = 0, 0
    while done < extra and tries < 30 * extra:
        tries += 1
        u = rng.choice(bush)
        w = rng.choice(nbrs[u])
        x = rng.choice(nbrs[w])
        if x == u or x not in bush_set or (min(u, x), max(u, x)) in edges:
            continue
        add(u, x, rng.randint(1, 60))
        done += 1

    assert nxt[0] == V

    # hide the structure: shuffle every id except the HQ
    labels = list(range(1, V))
    shuffled = labels[:]
    rng.shuffle(shuffled)
    nid = {0: 0}
    nid.update(zip(labels, shuffled))

    loc_type, loc_pen = [None] * V, [None] * V
    for l in range(V):
        loc_type[nid[l]], loc_pen[nid[l]] = typ[l], pen[l]
    items = list(edges.items())
    rng.shuffle(items)
    E = len(items)
    road_rows, adj = [], [[] for _ in range(V)]
    for r, ((a, b), m) in enumerate(items):
        u, v = sorted((nid[a], nid[b]))
        road_rows.append([cid, r, u, v, m, rng.randint(1, 100)])
        adj[u].append((v, m + loc_pen[v]))
        adj[v].append((u, m + loc_pen[u]))
    tgt = [nid[t] for t in targets]

    # ---- self-check ----
    assert V - 1 <= E <= 3 * V
    ok = False
    for t in tgt:
        fewest, cheapest, far, low = _route_stats(V, adj, t)
        assert low >= 0, "not connected"
        assert far >= 500, f"longest distance only {far}"
        if fewest >= 1.5 * cheapest:
            ok = True
    assert ok, "no target shows the trap"

    waves = _make_waves(rng, E, rng.randint(3, 5))
    return {
        "locations": [[cid, i, loc_type[i], loc_pen[i]] for i in range(V)],
        "roads": road_rows,
        "waves": [[cid, wi, r] for wi, wv in enumerate(waves) for r in sorted(wv)],
        "targets": tgt, "V": V, "E": E,
    }

# ---------------------------------------------------------------- case 49
def _prefix_hits(log, prefix, L):
    n, c = len(log), 0
    i = log.find(prefix)
    while i != -1 and i <= n - L:
        c += 1
        i = log.find(prefix, i + 1)
    return c

def trap_radio_49(rng, cid):
    n = rng.randint(50_000, 100_000)
    R = rng.choice(ALPHABET)                                   # the repeated block (1 symbol)
    Q = rng.choice([c for c in ALPHABET if c != R])            # never appears in the log
    noise = [c for c in ALPHABET if c not in (R, Q)]

    log = [R] * n
    segs = n // 2000                                           # short noise patches
    slot = n // segs
    for s in range(segs):
        ln = rng.randint(50, 100)
        start = s * slot + rng.randint(0, slot - ln)
        for i in range(start, start + ln):
            log[i] = rng.choice(noise)
    log = "".join(log)

    lens = [2, 4, 8, 12, 20, 40]
    pats = [R * 2, R * 4] + [R * (L - 1) + Q for L in lens[2:]]
    counts = [count_occ(log, p) for p in pats]

    # ---- self-check ----
    assert sum(ch == R for ch in log) >= 0.9 * n
    for p, L in zip(pats[2:], lens[2:]):
        assert _prefix_hits(log, p[:-1], L) >= 0.5 * (n - L + 1)
    assert sum(c > 0 for c in counts) >= 2 and any(c == 0 for c in counts)

    parts, pos = [], 0
    while pos < n:
        size = min(rng.randint(2000, 10000), n - pos)
        parts.append(log[pos:pos + size])
        pos += size
    a, b = make_reports(rng, "L")
    return {
        "radio_log": [[cid, i + 1, t] for i, t in enumerate(parts)],
        "radio_patterns": [[cid, i, p, c] for i, (p, c) in enumerate(zip(pats, counts))],
        "radio_reports": [[cid, a, b]],
        "edit_bound": edit_distance(a, b),
    }