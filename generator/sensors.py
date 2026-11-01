import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RANGES, eff_tier

def gen_sensors(k, rng, cid):
    tier = eff_tier(k)
    N = rng.randint(*RANGES["sensors"][tier])
    kk = rng.randint(max(2, N // 4), N // 2)

    cover = sorted(rng.sample(range(N), kk))
    others = [v for v in range(N) if v not in set(cover)]

    edges = set()

    def add(a, b):
        edges.add((min(a, b), max(a, b)))

    order = cover[:]
    rng.shuffle(order)
    for a, b in zip(order, order[1:]):            # path through the cover
        add(a, b)
    for v in others:                              # every other node hangs on the cover
        add(v, rng.choice(cover))

    max_edges = N * (N - 1) // 2 - (N - kk) * (N - kk - 1) // 2
    target = min(max_edges, len(edges) + rng.randint(N // 2, 2 * N))
    tries = 0
    while len(edges) < target and tries < 100 * N:
        tries += 1
        a, b = rng.choice(cover), rng.randrange(N)
        if a != b:
            add(a, b)

    # ---- self-check ----
    cs = set(cover)
    assert len(edges) >= N - 1
    assert all(u < v and (u in cs or v in cs) for u, v in edges)
    assert 2 <= kk <= N / 2 and len(cs) == kk

    return {
        "sensor_edges": [[cid, u, v] for u, v in sorted(edges)],
        "sensor_cover": [[cid, c] for c in cover],
        "sensor_nodes": N,
        "sensor_k": kk,
    }