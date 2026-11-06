import sys, os, math
from config import RANGES, eff_tier

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# variety rule 3 buckets (rules per switch) for cases 20..45
BUCKETS = [(2.5, 3.4), (3.6, 4.7), (4.9, 5.9)]

def gen_safety(k, rng, cid):
    tier = eff_tier(k)
    nv = rng.randint(*RANGES["safety"][tier])

    lo, hi = (2.0, 6.0) if tier == "S" else BUCKETS[(k - 20) % 3]
    m = rng.randint(math.ceil(lo * nv), math.floor(hi * nv))

    planted = {j: rng.randint(0, 1) for j in range(1, nv + 1)}
    rules = []
    for _ in range(m):
        vs = rng.sample(range(1, nv + 1), 3)
        lits = [v if rng.random() < 0.5 else -v for v in vs]
        if not any((l > 0) == bool(planted[abs(l)]) for l in lits):
            j = rng.randrange(3)
            lits[j] = -lits[j]
        rules.append(lits)

    # ---- self-check ----
    for lits in rules:
        assert len({abs(l) for l in lits}) == 3 and all(l != 0 for l in lits)
        assert any((l > 0) == bool(planted[abs(l)]) for l in lits)
    ratio = m / nv
    assert 2.0 <= ratio <= 6.0
    if tier != "S":
        assert 2.5 <= ratio <= 6.0

    return {
        "safety_rules": [[cid, i + 1, *lits] for i, lits in enumerate(rules)],
        "safety_planted": [[cid, j, v] for j, v in planted.items()],
        "safety_vars": nv,
    }