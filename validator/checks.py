import sys, os, heapq
from collections import Counter, deque
from fractions import Fraction
from bisect import bisect_right
from itertools import combinations
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from config import RANGES, ALPHABET, PENALTIES, tier_of, scenario_of

AL = set(ALPHABET)
LENS = [2, 4, 8, 12, 20, 40]

def count_occ(text, pattern):
    count, index = 0, text.find(pattern)
    while index != -1:
        count += 1
        index = text.find(pattern, index + 1)
    return count

def edit_distance(a, b):
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1,
                               previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]

def bfs_hops(V, adjr, src=0, blocked=frozenset()):
    hops = [-1] * V
    hops[src] = 0
    queue = deque([src])
    while queue:
        x = queue.popleft()
        for y, road_no, _ in adjr[x]:
            if hops[y] < 0 and road_no not in blocked:
                hops[y] = hops[x] + 1
                queue.append(y)
    return hops

def route_info(V, adjr, target):
    inf = float("inf")
    hop, order, queue = [-1] * V, [0], deque([0])
    hop[0] = 0
    while queue:
        x = queue.popleft()
        for y, _, _ in adjr[x]:
            if hop[y] < 0:
                hop[y] = hop[x] + 1
                queue.append(y)
                order.append(y)
    fewest_cost = [inf] * V
    fewest_cost[0] = 0
    for x in order:
        for y, _, weight in adjr[x]:
            if hop[y] == hop[x] + 1 and fewest_cost[x] + weight < fewest_cost[y]:
                fewest_cost[y] = fewest_cost[x] + weight
    distances, heap = [inf] * V, [(0, 0)]
    distances[0] = 0
    while heap:
        distance, x = heapq.heappop(heap)
        if distance > distances[x]:
            continue
        for y, _, weight in adjr[x]:
            if distance + weight < distances[y]:
                distances[y] = distance + weight
                heapq.heappush(heap, (distances[y], y))
    return fewest_cost[target], distances[target]

def greedy_and_opt(crates, capacity):
    order = sorted(crates, key=lambda crate: (-Fraction(crate[2], crate[1]), crate[0]))
    left, greedy = capacity, 0
    for _, weight, value in order:
        if weight <= left:
            left, greedy = left - weight, greedy + value
    best = [0] * (capacity + 1)
    for _, weight, value in crates:
        for current in range(capacity, weight - 1, -1):
            best[current] = max(best[current], best[current - weight] + value)
    return greedy, best[capacity]

def tour_opt(points):
    n = len(points)
    if n == 1:
        return 0
    distances = [[abs(a[0] - b[0]) + abs(a[1] - b[1]) for b in points] for a in points]
    middle, inf = n - 1, float("inf")
    dp = [[inf] * middle for _ in range(1 << middle)]
    for j in range(middle):
        dp[1 << j][j] = distances[0][j + 1]
    for mask in range(1 << middle):
        for j in range(middle):
            current = dp[mask][j]
            if current == inf or not (mask >> j) & 1:
                continue
            for target in range(middle):
                if not (mask >> target) & 1:
                    new_mask = mask | (1 << target)
                    dp[new_mask][target] = min(dp[new_mask][target], current + distances[j + 1][target + 1])
    return min(dp[(1 << middle) - 1][j] + distances[j + 1][0] for j in range(middle))

def cover_min(nodes, edges):
    masks = [(1 << u) | (1 << v) for u, v in edges]
    for size in range(nodes + 1):
        for combination in combinations(range(nodes), size):
            selected = sum(1 << node for node in combination)
            if all(mask & selected for mask in masks):
                return size

def windows_opt(windows):
    windows = sorted(windows, key=lambda window: (window[1], window[0]))
    finishes = [window[1] for window in windows]
    counts, values = [0], [0]
    for start, finish, value in windows:
        previous = bisect_right(finishes, start)
        counts.append(max(counts[-1], counts[previous] + 1))
        values.append(max(values[-1], values[previous] + value))
    return counts[-1], values[-1]

def drum_opt(prices):
    best = [0] * (len(prices) + 1)
    for length in range(1, len(prices) + 1):
        best[length] = max(prices[j - 1] + best[length - j] for j in range(1, length + 1))
    return best[-1]

class Ctx:
    def __init__(self, cid, k, sheets):
        self.cid, self.k, self.S = cid, k, sheets
        self.tier, self.sc = tier_of(k), scenario_of(k)
        self.E, self.facts, self.adjr = [], {}, None

    def err(self, code, message):
        self.E.append(f"{code}: {message}")

    def rows(self, sheet):
        return self.S.get(sheet, [])

    def span(self, key):
        if self.k == 46 and key == "crates":
            return 1500, 3000
        if self.k == 47 and key == "crates":
            return 12, 60
        if self.k == 48 and key == "locations":
            return 1500, 3000
        if self.k == 49 and key == "radio":
            return 50000, 100000
        return RANGES[key]["L" if self.tier == "X" else self.tier]

    def inrange(self, key, number, what):
        low, high = self.span(key)
        if not low <= number <= high:
            self.err("V2", f"{what} = {number}, outside {low}..{high}")

    def ids(self, rows, column, start, what):
        values = [row[column] for row in rows]
        if values != list(range(start, start + len(rows))):
            self.err("V3", f"{what} are not consecutive from {start}")
            return False
        return True

def v_cases(c):
    rows = c.rows("cases")
    if len(rows) != 1:
        c.err("V1", f"{len(rows)} rows in cases sheet for this case")
        return
    row = c.row = rows[0]
    if row["case_no"] != c.k:
        c.err("V1", f"case_no {row['case_no']} != {c.k}")
    if row["group_seed"] != int(c.cid.split("-")[0]):
        c.err("V1", "group_seed does not match the case_id prefix")
    if row["tier"] != c.tier:
        c.err("V1", f"tier {row['tier']} should be {c.tier}")
    if row["scenario"] != c.sc:
        c.err("V1", f"scenario {row['scenario']} should be {c.sc}")

def v_crates(c):
    rows = c.rows("crates")
    c.inrange("crates", len(rows), "crate count")
    c.ids(rows, "crate_id", 1, "crate_id values")
    for name, (low, high) in {"cat": (0, 4), "weight": (1, 20), "value": (10, 100), "expiry": (0, 999)}.items():
        if any(not low <= row[name] <= high for row in rows):
            c.err("V2", f"crate {name} outside {low}..{high}")
    serials = [row["serial"] for row in rows]
    if len(set(serials)) != len(rows) or any(not 10_000_000 <= serial <= 99_999_999 for serial in serials):
        c.err("V2", "serials are not distinct 8-digit numbers")
    total, capacity = sum(row["weight"] for row in rows), c.row["capacity"]
    if c.k != 47 and (capacity < 1 or 10 * capacity < total or 10 * capacity > 7 * total):
        c.err("V2", f"capacity {capacity} not within 10%..70% of total weight {total}")
    c.crates = [(row["crate_id"], row["weight"], row["value"]) for row in rows]
    c.cats = [row["cat"] for row in rows]
    c.expiry = [row["expiry"] for row in rows]
    if c.tier == "S" or c.k == 47:
        c.facts["greedy"], c.facts["opt"] = greedy_and_opt(c.crates, capacity)
        c.facts["greedy_fail"] = c.facts["greedy"] < c.facts["opt"]

def v_network(c):
    locations, roads, waves = c.rows("locations"), c.rows("roads"), c.rows("waves")
    nodes, edge_count = len(locations), len(roads)
    c.inrange("locations", nodes, "location count")
    if not c.ids(locations, "loc_id", 0, "loc_id values"):
        return
    if any(row["type"] not in "DSHJ" or len(row["type"]) != 1 for row in locations):
        c.err("V2", "location type not in D, S, H, J")
    if any(row["penalty"] not in PENALTIES for row in locations):
        c.err("V2", "location penalty not in {0, 1, 2, 4, 6}")
    if not locations or locations[0]["type"] != "D" or locations[0]["penalty"] != 0:
        c.err("V3", "location 0 must be type D with penalty 0")
    types = [row["type"] for row in locations]
    if "S" not in types or "H" not in types:
        c.err("V2", "need at least one shelter and one hospital")
    if not nodes - 1 <= edge_count <= 3 * nodes:
        c.err("V2", f"road count {edge_count} outside {nodes - 1}..{3 * nodes}")
    if not c.ids(roads, "road_no", 0, "road_no values"):
        return
    seen = set()
    for road in roads:
        u, v = road["u"], road["v"]
        if not 0 <= u < v < nodes:
            c.err("V3", f"road {road['road_no']}: invalid endpoints ({u}, {v})")
        if (u, v) in seen:
            c.err("V3", f"road {road['road_no']}: repeated pair ({u}, {v})")
        seen.add((u, v))
        if not 1 <= road["minutes"] <= 60 or not 1 <= road["cable"] <= 100:
            c.err("V2", f"road {road['road_no']}: minutes or cable out of range")
    penalty = [row["penalty"] for row in locations]
    adjr = [[] for _ in range(nodes)]
    for road in roads:
        u, v, minutes = road["u"], road["v"], road["minutes"]
        adjr[u].append((v, road["road_no"], minutes + penalty[v]))
        adjr[v].append((u, road["road_no"], minutes + penalty[u]))
    c.V, c.Ecount, c.adjr, c.types, c.pen = nodes, edge_count, adjr, types, penalty
    c.avgdeg = Fraction(2 * edge_count, nodes)
    if min(bfs_hops(nodes, adjr)) < 0:
        c.err("V4", "network is not connected before closures")
    wave_numbers = sorted({row["wave_no"] for row in waves})
    if wave_numbers != list(range(len(wave_numbers))):
        c.err("V3", "wave_no values are not 0, 1, 2, ...")
    low, high = c.span("waves")
    if not low <= len(wave_numbers) <= high:
        c.err("V2", f"{len(wave_numbers)} waves, outside {low}..{high}")
    c.waves = {}
    all_roads = Counter()
    for wave in waves:
        c.waves.setdefault(wave["wave_no"], set()).add(wave["road_no"])
        all_roads[wave["road_no"]] += 1
        if not 0 <= wave["road_no"] < edge_count:
            c.err("V3", f"wave references missing road {wave['road_no']}")
    if any(count > 1 for count in all_roads.values()):
        c.err("V4", "waves are not disjoint")
    for number, road_set in c.waves.items():
        if not 1 <= len(road_set) <= max(1, edge_count // 4):
            c.err("V4", f"wave {number} has {len(road_set)} roads")
    targets = [c.row["target_0"], c.row["target_1"], c.row["target_2"]]
    c.targets = targets
    if len(set(targets)) != 3 or any(not 1 <= target < nodes or types[target] not in "SH" for target in targets):
        c.err("V3", f"targets {targets} must be 3 distinct shelters/hospitals")
    if c.tier == "S":
        c.facts["route_trap"] = any(route_info(nodes, adjr, target)[0] > route_info(nodes, adjr, target)[1] for target in targets)

def v_radio(c):
    parts = c.rows("radio_log")
    if [part["part"] for part in parts] != list(range(1, len(parts) + 1)):
        c.err("V5", "log parts are not numbered 1, 2, ... in order")
    for part in parts:
        if not 1 <= len(part["text"]) <= 10000 or set(part["text"]) - AL:
            c.err("V5", f"log part {part['part']} is invalid")
    log = "".join(part["text"] for part in parts)
    c.log = log
    c.inrange("radio", len(log), "log length")
    patterns = c.rows("radio_patterns")
    if [pattern["pattern_no"] for pattern in patterns] != list(range(6)):
        c.err("V3", "pattern_no must be exactly 0..5")
    if [len(pattern["pattern"]) for pattern in patterns] != LENS:
        c.err("V2", "pattern lengths must be 2, 4, 8, 12, 20, 40")
    counts = []
    for pattern in patterns:
        real = count_occ(log, pattern["pattern"])
        counts.append(real)
        if set(pattern["pattern"]) - AL or real != pattern["count"]:
            c.err("V5", f"pattern {pattern['pattern_no']} count or symbols invalid")
    if sum(count > 0 for count in counts) < 2 or all(count > 0 for count in counts):
        c.err("V5", "need at least two occurring patterns and one absent pattern")
    reports = c.rows("radio_reports")
    if len(reports) != 1:
        c.err("V3", "radio_reports must have exactly one row per case")
        return
    report = reports[0]
    for name in ("report_a", "report_b"):
        value = report[name]
        c.inrange("report", len(value), f"{name} length")
        if set(value) - AL:
            c.err("V5", f"{name} has symbols outside the alphabet")
    distance = edit_distance(report["report_a"], report["report_b"])
    bound = c.row["edit_bound"]
    if not distance <= bound <= len(report["report_a"]) + len(report["report_b"]):
        c.err("V5", f"edit_bound {bound}, true distance {distance}")

def v_windows(c):
    windows = c.rows("windows")
    c.inrange("windows", len(windows), "window count")
    c.ids(windows, "window_id", 1, "window_id values")
    starts = Counter(window["start"] for window in windows)
    if len(windows) >= 8 and sum(starts[window["finish"]] for window in windows) < 2:
        c.err("V2", "fewer than two touching window pairs")
    c.windows = [(row["start"], row["finish"], row["value"]) for row in windows]
    finishes = sorted(finish for _, finish, _ in c.windows)
    c.overlap_pairs = len(windows) * (len(windows) - 1) // 2 - sum(bisect_right(finishes, start) for start, _, _ in c.windows)

def v_incidents(c):
    incidents = c.rows("incidents")
    c.inrange("alarms", len(incidents), "alarm count")
    c.ids(incidents, "alarm_id", 1, "alarm_id values")
    ticks, priorities = [row["tick"] for row in incidents], [row["priority"] for row in incidents]
    if not ticks or ticks[0] != 0 or any(a > b for a, b in zip(ticks, ticks[1:])):
        c.err("V2", "ticks must start at 0 and never decrease")
    if any(not 1 <= priority <= 10 for priority in priorities):
        c.err("V2", "priority outside 1..10")
    c.n_alarms, c.ticks_n, c.pr = len(incidents), ticks[-1] + 1, priorities
    if c.tier in ("M", "L"):
        if not 5 * len(incidents) >= 6 * c.ticks_n and 5 * len(incidents) <= 9 * c.ticks_n:
            c.err("V2", "alarms per tick outside 1.2..1.8")
        if len(set(priorities)) < 6 or 1 not in priorities:
            c.err("V2", "need at least 6 distinct priorities including 1")

def v_sites(c):
    sites = c.rows("sites")
    c.inrange("sites", len(sites), "site count")
    c.ids(sites, "site_no", 0, "site_no values")
    points = [(row["x"], row["y"]) for row in sites]
    if len(set(points)) != len(points):
        c.err("V2", "two sites are equal")
    c.pts = points
    tour = c.rows("tour")
    c.ids(tour, "step", 0, "tour steps")
    sequence = [row["site_no"] for row in tour]
    if sorted(sequence) != list(range(len(sites))) or not sequence or sequence[0] != 0:
        c.err("V6", "tour is not a permutation starting at site 0")
        return
    distance = lambda a, b: abs(points[a][0] - points[b][0]) + abs(points[a][1] - points[b][1])
    length = sum(distance(sequence[i], sequence[(i + 1) % len(sequence)]) for i in range(len(sequence)))
    if length != c.row["tour_length"]:
        c.err("V6", "tour_length does not match the closed tour")
    if c.tier in ("L", "X"):
        seen, current, nearest = {0}, 0, 0
        for _ in range(len(points) - 1):
            next_site = min((j for j in range(len(points)) if j not in seen), key=lambda j: (distance(current, j), j))
            nearest += distance(current, next_site)
            seen.add(next_site)
            current = next_site
        if length > nearest + distance(current, 0):
            c.err("V6", "tour is longer than nearest-neighbour tour")

def v_chains(c):
    dimensions, drums = c.rows("pipeline_dims"), c.rows("drum_prices")
    c.ids(dimensions, "idx", 0, "pipeline idx values")
    c.inrange("stages", len(dimensions) - 1, "pipeline stages")
    c.ids(drums, "length", 1, "drum lengths")
    c.inrange("drum", len(drums), "drum length")
    prices = [row["price"] for row in drums]
    if all(price == prices[0] * length for length, price in enumerate(prices, 1)):
        c.err("V2", "drum prices are all proportional to length")
    c.prices = prices

def v_sensors(c):
    nodes, cover_size = c.row["sensor_nodes"], c.row["sensor_k"]
    c.inrange("sensors", nodes, "sensor_nodes")
    edges = [(row["u"], row["v"]) for row in c.rows("sensor_edges")]
    if any(not 0 <= u < v < nodes for u, v in edges) or len(set(edges)) != len(edges):
        c.err("V3", "sensor edges have invalid endpoints or duplicates")
    if len(edges) < nodes - 1:
        c.err("V2", "not enough sensor edges")
    cover = [row["node"] for row in c.rows("sensor_cover")]
    if len(set(cover)) != len(cover) or any(not 0 <= node < nodes for node in cover):
        c.err("V3", "sensor cover has invalid or repeated nodes")
    if len(cover) != cover_size or not 2 <= cover_size <= nodes // 2:
        c.err("V6", "sensor cover size is invalid")
    selected = set(cover)
    if any(u not in selected and v not in selected for u, v in edges):
        c.err("V6", "planted cover misses an edge")
    c.sedges, c.N = edges, nodes

def v_safety(c):
    variables = c.row["safety_vars"]
    c.inrange("safety", variables, "safety_vars")
    rules, planted = c.rows("safety_rules"), c.rows("safety_planted")
    c.ids(rules, "rule_no", 1, "rule_no values")
    if [row["switch"] for row in planted] != list(range(1, variables + 1)):
        c.err("V3", "safety_planted must list switches 1..safety_vars")
    values = {row["switch"]: row["value"] for row in planted}
    if any(row["value"] not in (0, 1) for row in planted):
        c.err("V3", "planted switch value must be 0 or 1")
    if not 2 * variables <= len(rules) <= 6 * variables:
        c.err("V2", "rules per switch outside 2.0..6.0")
    c.safety_ratio = Fraction(len(rules), variables)
    for rule in rules:
        literals = [rule["lit_1"], rule["lit_2"], rule["lit_3"]]
        if 0 in literals or len({abs(literal) for literal in literals}) != 3 or any(abs(literal) > variables for literal in literals):
            c.err("V3", f"rule {rule['rule_no']} is malformed")
        elif not any((literal > 0) == bool(values.get(abs(literal), 0)) for literal in literals):
            c.err("V6", f"planted assignment breaks rule {rule['rule_no']}")

def v_rations(c):
    rations = c.rows("rations")
    c.inrange("rations", len(rations), "ration count")
    c.ids(rations, "item", 0, "ration items")
    if any(not 1 <= row["value"] <= 1000 for row in rations):
        c.err("V2", "ration value outside 1..1000")
    total = sum(row["value"] for row in rations if row["planted"] == 1)
    if total != c.row["rations_target"]:
        c.err("V6", "planted rations do not match rations_target")

def v_claims(c):
    claims = c.rows("claims")
    if c.tier != "S":
        if claims:
            c.err("V5", "claims are for tier S only")
        return
    if len(claims) != 1:
        c.err("V5", "tier S case needs exactly one claims row")
        return
    claim = claims[0]
    cargo = greedy_and_opt(c.crates, c.row["capacity"])[1]
    window_count, window_value = windows_opt(c.windows)
    truth = {"cargo_opt": cargo, "window_count_opt": window_count,
             "window_value_opt": window_value, "drum_opt": drum_opt(c.prices),
             "tour_opt": tour_opt(c.pts), "cover_min": cover_min(c.N, c.sedges)}
    for key, value in truth.items():
        if claim[key] != value:
            c.err("V5", f"claim {key} = {claim[key]}, recomputed {value}")

def v_signature(c):
    if c.k > 45:
        return
    scenario, count = c.sc, len(c.cats)
    share = lambda categories: sum(value in categories for value in c.cats)
    wave_count = len(c.waves)
    if scenario == 1:
        if not Fraction(22, 10) <= c.avgdeg <= Fraction(32, 10): c.err("V7", "study 1 average degree")
        if 5 * sum(penalty >= 2 for penalty in c.pen) < 2 * c.V: c.err("V7", "study 1 penalty share")
        if wave_count < 3: c.err("V7", "study 1 wave count")
        if 100 * share({0, 1}) < 55 * count: c.err("V7", "study 1 category share")
    elif scenario == 2:
        if not 2 <= c.avgdeg <= Fraction(26, 10): c.err("V7", "study 2 average degree")
        if 100 * share({2, 3}) < 45 * count: c.err("V7", "study 2 category share")
        if sum(c.pr) < 6 * c.n_alarms: c.err("V7", "study 2 priority mean")
    elif scenario == 3:
        if 4 * c.types.count("S") < c.V: c.err("V7", "study 3 shelter share")
        if wave_count < 3: c.err("V7", "study 3 wave count")
        if len(c.windows) and c.overlap_pairs < len(c.windows): c.err("V7", "study 3 overlap")
        if len(set(c.log)) < 30: c.err("V7", "study 3 alphabet coverage")
    elif scenario == 4:
        if c.avgdeg < Fraction(7, 2): c.err("V7", "study 4 average degree")
        if c.tier in ("M", "L") and 2 * c.n_alarms < 3 * c.ticks_n: c.err("V7", "study 4 alarm rate")
        if 10 * share({4}) < count: c.err("V7", "study 4 rare share")
    elif scenario == 5:
        if c.avgdeg > Fraction(12, 5): c.err("V7", "study 5 average degree")
        if max(len(adj) for adj in c.adjr) > 4: c.err("V7", "study 5 maximum degree")
        if max(bfs_hops(c.V, c.adjr)) < c.V // 4: c.err("V7", "study 5 graph diameter")
        if wave_count < 3: c.err("V7", "study 5 wave count")
        blocked = set().union(*c.waves.values()) if c.waves else set()
        if all(hop >= 0 for hop in bfs_hops(c.V, c.adjr, 0, blocked) for _ in [hop]):
            pass
        if all(bfs_hops(c.V, c.adjr, 0, blocked)[target] >= 0 for target in c.targets): c.err("V7", "study 5 target cut-off")
    elif scenario == 6:
        if 100 * share({2, 1}) < 55 * count: c.err("V7", "study 6 category share")
        if 2 * sum(expiry <= 300 for expiry in c.expiry) < count: c.err("V7", "study 6 expiry share")
        if 4 * max(Counter(c.log).values()) < len(c.log): c.err("V7", "study 6 dominant symbol")

def v_traps(c):
    if c.k < 46:
        return
    if c.k == 46:
        fields = {"value": [crate[2] for crate in c.crates], "weight": [crate[1] for crate in c.crates],
                  "expiry": c.expiry, "ratio": [Fraction(crate[2], crate[1]) for crate in c.crates],
                  "serial": [row["serial"] for row in c.rows("crates")]}
        mono = lambda values: all(a <= b for a, b in zip(values, values[1:])) or all(a >= b for a, b in zip(values, values[1:]))
        if sum(mono(values) for values in fields.values()) < 3: c.err("V8", "trap 46 monotonic fields")
    elif c.k == 47:
        if 10 * c.facts["greedy"] > 6 * c.facts["opt"]: c.err("V8", "trap 47 greedy ratio")
    elif c.k == 48:
        farthest = bfs_hops(c.V, c.adjr, 0).index(max(bfs_hops(c.V, c.adjr, 0)))
        if max(bfs_hops(c.V, c.adjr, farthest)) < 500: c.err("V8", "trap 48 longest distance")
        if not any(2 * route_info(c.V, c.adjr, target)[0] >= 3 * route_info(c.V, c.adjr, target)[1] for target in c.targets):
            c.err("V8", "trap 48 route trap")
    elif c.k == 49:
        log = c.log
        best = max(sum(Counter(log[offset::block]).most_common(1)[0][1] for offset in range(block)) for block in range(1, 9))
        if 10 * best < 9 * len(log): c.err("V8", "trap 49 repeated block")
        near = 0
        for pattern in c.rows("radio_patterns"):
            length, prefix = len(pattern["pattern"]), pattern["pattern"][:-1]
            hits, index = 0, log.find(prefix)
            while index != -1 and index <= len(log) - length:
                hits += 1
                index = log.find(prefix, index + 1)
            near += 2 * hits >= len(log) - length + 1
        if near < 4: c.err("V8", "trap 49 near-miss patterns")

ORDER = [v_cases, v_crates, v_network, v_radio, v_windows, v_incidents, v_sites,
         v_chains, v_sensors, v_safety, v_rations, v_claims, v_signature, v_traps]

def check_case(cid, k, sheets):
    context = Ctx(cid, k, sheets)
    for function in ORDER:
        if function is not v_cases and not hasattr(context, "row"):
            break
        try:
            function(context)
        except Exception as error:
            context.err("V1", f"{function.__name__} could not run ({type(error).__name__}: {error})")
    modules = {name: name for name in ("crates", "locations", "roads", "windows", "incidents", "sites", "pipeline_dims", "drum_prices", "sensor_edges", "safety_rules", "rations")}
    fingerprints = {}
    for name, sheet in modules.items():
        rows = sheets.get(sheet, [])
        if len(rows) >= 8:
            fingerprints[name] = hash(tuple(tuple(value for header, value in row.items() if header != "case_id") for row in rows))
    if len(getattr(context, "log", "")) >= 8:
        fingerprints["radio_log"] = hash(context.log)
    context.facts["fingerprints"] = fingerprints
    context.facts["safety_ratio"] = getattr(context, "safety_ratio", None)
    return context.E, context.facts