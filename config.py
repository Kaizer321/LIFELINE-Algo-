# config.py  -- shared constants for generator and validator
SEED = 69

SHEETS = [
    "cases", "crates", "locations", "roads", "waves", "radio_log",
    "radio_patterns", "radio_reports", "windows", "incidents", "sites",
    "tour", "pipeline_dims", "drum_prices", "sensor_edges", "sensor_cover",
    "safety_rules", "safety_planted", "rations", "claims",
]

HEADERS = {
    "cases": ["case_id","group_seed","case_no","tier","scenario","capacity",
              "target_0","target_1","target_2","edit_bound","tour_length",
              "sensor_nodes","sensor_k","safety_vars","rations_target"],
    "crates": ["case_id","crate_id","cat","weight","value","expiry","serial"],
    "locations": ["case_id","loc_id","type","penalty"],
    "roads": ["case_id","road_no","u","v","minutes","cable"],
    "waves": ["case_id","wave_no","road_no"],
    "radio_log": ["case_id","part","text"],
    "radio_patterns": ["case_id","pattern_no","pattern","count"],
    "radio_reports": ["case_id","report_a","report_b"],
    "windows": ["case_id","window_id","start","finish","value"],
    "incidents": ["case_id","alarm_id","tick","priority"],
    "sites": ["case_id","site_no","x","y"],
    "tour": ["case_id","step","site_no"],
    "pipeline_dims": ["case_id","idx","dim"],
    "drum_prices": ["case_id","length","price"],
    "sensor_edges": ["case_id","u","v"],
    "sensor_cover": ["case_id","node"],
    "safety_rules": ["case_id","rule_no","lit_1","lit_2","lit_3"],
    "safety_planted": ["case_id","switch","value"],
    "rations": ["case_id","item","value","planted"],
    "claims": ["case_id","cargo_opt","window_count_opt","window_value_opt",
               "drum_opt","tour_opt","cover_min"],
}

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"   # 38 symbols
PENALTIES = [0, 1, 2, 4, 6]
LOC_TYPES = ["D", "S", "H", "J"]
CATS = {0: "Food", 1: "Water", 2: "Medicine", 3: "Tool", 4: "Rare"}

def tier_of(k):
    if k < 20: return "S"
    if k < 40: return "M"
    if k < 46: return "L"
    return "X"

def eff_tier(k):
    t = tier_of(k)
    return "L" if t == "X" else t

def scenario_of(k):
    return (k % 6) + 1

def case_id(k):
    return f"{SEED}-{k:02d}"          # e.g. 69-07

# Ranges by tier: (min, max)
RANGES = {
    "crates":    {"S": (8, 20),  "M": (40, 200),     "L": (500, 1500)},
    "locations": {"S": (6, 12),  "M": (30, 150),     "L": (500, 2000)},
    "waves":     {"S": (2, 5),   "M": (2, 5),        "L": (2, 5)},
    "radio":     {"S": (200, 500), "M": (2000, 10000), "L": (20000, 100000)},
    "report":    {"S": (10, 30), "M": (30, 150),     "L": (200, 1000)},
    "windows":   {"S": (8, 20),  "M": (50, 300),     "L": (1000, 3000)},
    "alarms":    {"S": (10, 40), "M": (200, 1000),   "L": (2000, 5000)},
    "sites":     {"S": (5, 9),   "M": (10, 16),      "L": (200, 500)},
    "stages":    {"S": (4, 8),   "M": (15, 60),      "L": (100, 300)},
    "drum":      {"S": (5, 14),  "M": (40, 200),     "L": (500, 2000)},
    "sensors":   {"S": (6, 14),  "M": (20, 40),      "L": (100, 400)},
    "safety":    {"S": (6, 15),  "M": (20, 50),      "L": (20, 50)},
    "rations":   {"S": (8, 20),  "M": (24, 40),      "L": (50, 100)},
}
# Tier X uses the tier L ranges unless a trap says otherwise.