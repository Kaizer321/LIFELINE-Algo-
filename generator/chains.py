import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RANGES, tier_of

def gen_chains(k, rng, cid):
    tier = tier_of(k)
    if tier == "X":
        raise NotImplementedError("trap cases 46-49 handled separately")

    # pipeline: n stages -> n + 1 dimensions
    n = rng.randint(*RANGES["stages"][tier])
    dims = [rng.randint(2, 100) for _ in range(n + 1)]

    # drum prices for lengths 1..L
    L = rng.randint(*RANGES["drum"][tier])
    expo = rng.uniform(0.6, 0.9)
    prices = []
    for j in range(1, L + 1):
        base = 500 * (j / L) ** expo
        prices.append(min(500, max(1, round(base * rng.uniform(0.7, 1.1)))))

    # ---- self-check ----
    assert len(dims) == n + 1 and all(2 <= d <= 100 for d in dims)
    assert len(prices) == L and all(1 <= p <= 500 for p in prices)
    assert any(prices[j - 1] * 1 != prices[0] * j for j in range(1, L + 1)), \
        "prices are all proportional to length"

    return {
        "pipeline_dims": [[cid, i, d] for i, d in enumerate(dims)],
        "drum_prices": [[cid, j, p] for j, p in enumerate(prices, 1)],
    }