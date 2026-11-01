import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RANGES, eff_tier, scenario_of

SC2_WEIGHTS = [1, 1, 1, 1, 2, 3, 5, 6, 6, 6]     # priorities 1..10, mean about 7.3

def gen_incidents(k, rng, cid):
    tier = eff_tier(k)
    sc = scenario_of(k)
    lo, hi = RANGES["alarms"][tier]
    n = rng.randint(lo, hi)

    # number of ticks L, so the last tick is L - 1
    if tier == "S":
        L = rng.randint(max(4, n // 3), 2 * n)
    else:
        rlo, rhi = (1.52, 1.78) if sc == 4 else (1.22, 1.78)
        L = rng.randint(math.ceil(n / rhi), math.floor(n / rlo))

    ticks = []
    if sc == 2:                                   # bursts after aftershocks
        centers = [rng.randint(0, L - 1) for _ in range(max(2, L // 40))]
        for _ in range(n):
            if rng.random() < 0.7:
                t = int(rng.gauss(rng.choice(centers), max(1, L / 60)))
                t = min(max(t, 0), L - 1)
            else:
                t = rng.randint(0, L - 1)
            ticks.append(t)
    else:
        ticks = [rng.randint(0, L - 1) for _ in range(n)]
    ticks.sort()
    ticks[0], ticks[-1] = 0, L - 1

    weights = SC2_WEIGHTS if sc == 2 else [1] * 10
    for _ in range(2000):
        pr = rng.choices(range(1, 11), weights=weights, k=n)
        if tier != "S" and not (1 in pr and len(set(pr)) >= 6):
            continue
        if sc == 2 and sum(pr) / n < 6.05:
            continue
        break
    else:
        raise RuntimeError("could not build priorities")

    # ---- self-check ----
    assert ticks[0] == 0 and all(a <= b for a, b in zip(ticks, ticks[1:]))
    assert all(1 <= p <= 10 for p in pr)
    if tier != "S":
        rate = n / (ticks[-1] + 1)
        assert 1.2 <= rate <= 1.8, rate
        assert len(set(pr)) >= 6 and 1 in pr
        if sc == 4:
            assert rate >= 1.5
    if sc == 2:
        assert sum(pr) / n >= 6.0

    return [[cid, i + 1, ticks[i], pr[i]] for i in range(n)]