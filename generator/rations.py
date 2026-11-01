import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RANGES, tier_of

def gen_rations(k, rng, cid):
    tier = tier_of(k)
    if tier == "X":
        raise NotImplementedError("trap cases 46-49 handled separately")
    n = rng.randint(*RANGES["rations"][tier])
    values = [rng.randint(1, 1000) for _ in range(n)]
    size = rng.randint(max(2, n // 4), max(2, n // 2))
    chosen = set(rng.sample(range(n), size))
    target = sum(values[i] for i in chosen)

    # ---- self-check ----
    assert target > 0 and all(1 <= v <= 1000 for v in values)
    assert sum(v for i, v in enumerate(values) if i in chosen) == target

    return {
        "rations": [[cid, i, values[i], 1 if i in chosen else 0] for i in range(n)],
        "rations_target": target,
    }