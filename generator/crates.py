import math, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RANGES, tier_of, scenario_of

# category share rules per case study: (set of categories, min share)
CAT_RULES = {
    1: ({0, 1}, 0.55),
    2: ({2, 3}, 0.45),
    4: ({4}, 0.10),
    6: ({2, 1}, 0.55),
}

def gen_crates(k, rng, cid):
    tier = tier_of(k)
    if tier == "X":
        raise NotImplementedError("trap cases 46-49 handled separately")
    sc = scenario_of(k)
    lo, hi = RANGES["crates"][tier]
    n = rng.randint(lo, hi)

    # categories: guarantee the minimum share exactly, then fill the rest randomly
    cats = []
    if sc in CAT_RULES:
        special, share = CAT_RULES[sc]
        need = min(n, math.ceil(share * n) + 1)        # +1 margin
        cats += [rng.choice(sorted(special)) for _ in range(need)]
    while len(cats) < n:
        cats.append(rng.randint(0, 4))
    rng.shuffle(cats)

    # expiry: study 6 needs at least half expiring by hour 300
    expiry = [rng.randint(0, 999) for _ in range(n)]
    if sc == 6:
        for i in rng.sample(range(n), math.ceil(n / 2) + 1 if n > 1 else 1):
            expiry[i] = rng.randint(0, 300)

    # distinct 8-digit serials
    serials = set()
    while len(serials) < n:
        serials.add(rng.randint(10_000_000, 99_999_999))
    serials = list(serials)
    rng.shuffle(serials)

    rows = []
    for i in range(n):
        rows.append([cid, i + 1, cats[i], rng.randint(1, 20),
                     rng.randint(10, 100), expiry[i], serials[i]])
    return rows