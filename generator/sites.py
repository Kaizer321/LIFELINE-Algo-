import sys, os
from config import RANGES, eff_tier

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def closed_len(pts, tour):
    return sum(dist(pts[tour[i]], pts[tour[(i + 1) % len(tour)]])
               for i in range(len(tour)))

def nn_tour(pts):
    """Nearest unvisited site from site 0; ties go to the lowest site_no."""
    n = len(pts)
    seen = [False] * n
    seen[0] = True
    tour, cur = [0], 0
    for _ in range(n - 1):
        best, bd = -1, None
        for j in range(n):
            if not seen[j]:
                d = dist(pts[cur], pts[j])
                if bd is None or d < bd:
                    best, bd = j, d
        seen[best] = True
        tour.append(best)
        cur = best
    return tour

def two_opt(pts, tour, max_passes=30):
    n = len(tour)
    t = tour[:]
    for _ in range(max_passes):
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a, b = pts[t[i - 1]], pts[t[i]]
                c, d = pts[t[j]], pts[t[(j + 1) % n]]
                if dist(a, c) + dist(b, d) < dist(a, b) + dist(c, d):
                    t[i:j + 1] = reversed(t[i:j + 1])
                    improved = True
        if not improved:
            break
    return t

def gen_sites(k, rng, cid):
    tier = eff_tier(k)
    lo, hi = RANGES["sites"][tier]
    n = rng.randint(lo, hi)

    pts, used = [], set()
    while len(pts) < n:
        p = (rng.randint(0, 999), rng.randint(0, 999))
        if p not in used:
            used.add(p)
            pts.append(p)

    nn = nn_tour(pts)
    tour = two_opt(pts, nn)
    length = closed_len(pts, tour)

    # ---- self-check ----
    assert sorted(tour) == list(range(n)) and tour[0] == 0
    assert len(used) == n
    if tier in ("L", "X"):
        assert length <= closed_len(pts, nn), "planted tour longer than NN"

    return {
        "sites": [[cid, i, x, y] for i, (x, y) in enumerate(pts)],
        "tour": [[cid, s, site] for s, site in enumerate(tour)],
        "tour_length": length,
    }