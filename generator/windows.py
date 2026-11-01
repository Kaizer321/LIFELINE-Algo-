import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from bisect import bisect_right
from collections import Counter
from config import RANGES, eff_tier, scenario_of

def avg_overlap(ws):
    """Average number of other windows each window strictly overlaps."""
    n = len(ws)
    fins = sorted(f for _, f, _ in ws)
    disjoint = sum(bisect_right(fins, s) for s, _, _ in ws)   # pairs with f_i <= s_j
    overlapping = n * (n - 1) // 2 - disjoint
    return 2 * overlapping / n

def _once(rng, n, dmax, span):
    dm = min(dmax, span // 2)
    npairs = 2 if n < 12 else 3
    ws = []
    for _ in range(npairs):                      # touching pairs
        d1, d2 = rng.randint(5, dm), rng.randint(5, dm)
        s = rng.randint(0, span - d1 - d2)
        ws.append((s, s + d1, rng.randint(1, 100)))
        ws.append((s + d1, s + d1 + d2, rng.randint(1, 100)))
    while len(ws) < n:
        d = rng.randint(5, dm)
        s = rng.randint(0, span - d)
        ws.append((s, s + d, rng.randint(1, 100)))
    rng.shuffle(ws)
    return ws

def gen_windows(k, rng, cid):
    tier = eff_tier(k)
    sc = scenario_of(k)
    lo, hi = RANGES["windows"][tier]
    n = rng.randint(lo, hi)

    if sc == 3:
        for attempt in range(3000):
            dmax = min(480, 40 + (attempt // 5) * 10)
            span = 1440 if n >= 50 else max(720, 1440 - attempt)
            ws = _once(rng, n, dmax, span)
            if avg_overlap(ws) >= 2.2:
                break
        else:
            raise RuntimeError("could not reach overlap for study 3")
    else:
        ws = _once(rng, n, 300, 1440)

    # ---- self-check ----
    for s, f, v in ws:
        assert 0 <= s < f <= 1440 and 5 <= f - s <= 480 and 1 <= v <= 100
    starts = Counter(s for s, _, _ in ws)
    touching = sum(starts[f] for _, f, _ in ws)
    assert touching >= 2, "need at least two touching pairs"
    if sc == 3:
        assert avg_overlap(ws) >= 2.0

    return [[cid, i + 1, s, f, v] for i, (s, f, v) in enumerate(ws)]