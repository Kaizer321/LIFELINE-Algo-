import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from collections import Counter
from config import RANGES, ALPHABET, eff_tier, scenario_of

LENS = [2, 4, 8, 12, 20, 40]
WORDCH = ALPHABET[:36]            # A-Z and 0-9

def count_occ(text, p):
    """Occurrences of p in text, overlaps included."""
    c, i = 0, text.find(p)
    while i != -1:
        c += 1
        i = text.find(p, i + 1)
    return c

def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

def _word(rng, lo=3, hi=8):
    return "".join(rng.choice(WORDCH) for _ in range(rng.randint(lo, hi)))

def make_log(rng, n, sc):
    if sc == 6:                                   # repeating beacons
        sym = rng.choice("_-0")
        beacons = [_word(rng, 4, 8) + sym * rng.randint(2, 4) for _ in range(6)]
        out, total = [], 0
        while total < n:
            b = rng.choice(beacons)
            out.append(b)
            total += len(b)
        log = list("".join(out)[:n])
        need = math.ceil(0.27 * n)
        have = log.count(sym)
        if have < need:
            idx = [i for i, c in enumerate(log) if c != sym]
            for i in rng.sample(idx, need - have):
                log[i] = sym
        return "".join(log)

    vocab = [_word(rng) for _ in range(rng.randint(12, 30))]
    out, total = [], 0
    while total < n:
        w = rng.choice(vocab) + rng.choice("_-")
        out.append(w)
        total += len(w)
    log = list("".join(out)[:n])

    if sc == 3:                                   # noisy radio
        for i in range(n):
            if rng.random() < 0.12:
                log[i] = rng.choice(ALPHABET)
        for _ in range(5):                        # make sure all symbols appear
            present = set(log)
            missing = [c for c in ALPHABET if c not in present]
            if not missing:
                break
            for c, i in zip(missing, rng.sample(range(n), len(missing))):
                log[i] = c
    return "".join(log)

def make_patterns(rng, log):
    absent = rng.choice([3, 4, 5])                # this one must NOT occur
    pats = []
    for idx, L in enumerate(LENS):
        want_random = (idx == absent) or (idx >= 3 and rng.random() < 0.3)
        if want_random:
            for _ in range(500):
                p = "".join(rng.choice(ALPHABET) for _ in range(L))
                if count_occ(log, p) == 0:
                    break
            else:
                raise RuntimeError("could not build an absent pattern")
        else:
            s = rng.randrange(len(log) - L + 1)
            p = log[s:s + L]
        pats.append(p)
    return pats

def make_reports(rng, tier):
    lo, hi = RANGES["report"][tier]
    la = rng.randint(lo, hi)
    a = "".join(rng.choice(ALPHABET) for _ in range(la))
    while True:
        b = list(a)
        for _ in range(rng.randint(2, max(3, la // 4))):
            op = rng.choice("ids")
            if op == "i" and len(b) < hi:
                b.insert(rng.randint(0, len(b)), rng.choice(ALPHABET))
            elif op == "d" and len(b) > lo:
                del b[rng.randrange(len(b))]
            elif op == "s":
                b[rng.randrange(len(b))] = rng.choice(ALPHABET)
        b = "".join(b)
        if b != a:
            return a, b

def gen_radio(k, rng, cid):
    tier = eff_tier(k)
    sc = scenario_of(k)
    lo, hi = RANGES["radio"][tier]
    n = rng.randint(lo, hi)
    log = make_log(rng, n, sc)
    pats = make_patterns(rng, log)
    a, b = make_reports(rng, tier)
    bound = edit_distance(a, b)

    # ---- self-check ----
    assert set(log) <= set(ALPHABET) and len(log) == n
    if sc == 3:
        assert len(set(log)) >= 30, "study 3 needs 30 symbols"
    if sc == 6:
        assert max(Counter(log).values()) >= 0.25 * n, "study 6 dominant symbol"
    counts = [count_occ(log, p) for p in pats]
    assert sum(c > 0 for c in counts) >= 2 and any(c == 0 for c in counts)
    assert bound <= len(a) + len(b)

    parts, pos = [], 0
    while pos < n:
        size = min(rng.randint(2000, 10000), n - pos)
        parts.append(log[pos:pos + size])
        pos += size
    return {
        "radio_log": [[cid, i + 1, t] for i, t in enumerate(parts)],
        "radio_patterns": [[cid, i, p, c] for i, (p, c) in enumerate(zip(pats, counts))],
        "radio_reports": [[cid, a, b]],
        "edit_bound": bound,
    }