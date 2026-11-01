import os, re, sys
from collections import defaultdict
from fractions import Fraction
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from load import load
from checks import check_case

ID = re.compile(r"^(\d+)-(\d{2})$")

def validate_file(path, partial=False):
    data, global_errors = load(path)
    by_case = defaultdict(lambda: defaultdict(list))
    for sheet, rows in data.items():
        for row in rows:
            by_case[row["case_id"]][sheet].append(row)
    case_ids = [row["case_id"] for row in data.get("cases", [])]
    seeds = set()
    for case_id in by_case:
        match = ID.match(case_id)
        if not match:
            global_errors.append(f"V1: case_id {case_id!r} is not in the format <seed>-<kk>")
        else:
            seeds.add(match.group(1))
    if len(seeds) > 1:
        global_errors.append(f"V1: several group seeds in case_ids: {sorted(seeds)}")
    if len(case_ids) != len(set(case_ids)):
        global_errors.append("V1: duplicate case_id in the cases sheet")
    for case_id in by_case:
        if case_id not in case_ids:
            global_errors.append(f"V1: case_id {case_id} appears in a sheet but not in cases")
    if not partial:
        seed = next(iter(seeds), "?")
        expected = [f"{seed}-{k:02d}" for k in range(50)]
        if sorted(set(case_ids)) != expected:
            global_errors.append(f"V1: expected exactly the 50 case_ids {expected[0]} .. {expected[-1]}")
    results, facts = {}, {}
    for case_id in sorted(by_case):
        match = ID.match(case_id)
        if match:
            results[case_id], facts[case_id] = check_case(case_id, int(match.group(2)), by_case[case_id])
    if not partial:
        indices = {case_id: int(case_id.split("-")[1]) for case_id in facts}
        tier_s = [case_id for case_id in facts if indices[case_id] < 20]
        if sum(bool(facts[case_id].get("greedy_fail")) for case_id in tier_s) < 5:
            global_errors.append("V7: variety 1: too few greedy failures")
        if sum(bool(facts[case_id].get("route_trap")) for case_id in tier_s) < 5:
            global_errors.append("V7: variety 2: too few route traps")
        ratios = [facts[case_id]["safety_ratio"] for case_id in facts if 20 <= indices[case_id] <= 45]
        if len(ratios) != 26 or None in ratios:
            global_errors.append("V7: variety 3: need safety ratios for all 26 cases")
        else:
            low = sum(ratio < Fraction(7, 2) for ratio in ratios)
            middle = sum(Fraction(7, 2) <= ratio <= Fraction(24, 5) for ratio in ratios)
            high = sum(ratio > Fraction(24, 5) for ratio in ratios)
            if low < 5 or middle < 8 or high < 5:
                global_errors.append(f"V7: variety 3 buckets = ({low}, {middle}, {high})")
        seen = {}
        for case_id in sorted(facts):
            for module, fingerprint in facts[case_id].get("fingerprints", {}).items():
                if (module, fingerprint) in seen:
                    global_errors.append(f"V7: variety 4: cases {seen[(module, fingerprint)]} and {case_id} are equal in module {module}")
                else:
                    seen[(module, fingerprint)] = case_id
    return global_errors, results

def print_result(global_errors, results, out=sys.stdout):
    for error in global_errors:
        print(f"GLOBAL  {error}", file=out)
    for case_id, errors in results.items():
        print(f"{case_id}  {'PASS' if not errors else 'FAIL'}", file=out)
        for error in errors:
            print(f"    {error}", file=out)
    failed = sum(bool(errors) for errors in results.values())
    passed = not global_errors and not failed
    print(f"\nRESULT: {'PASS' if passed else 'FAIL'}  ({len(results) - failed}/{len(results)} cases pass, {len(global_errors)} global problems)", file=out)
    return passed

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "cases.xlsx"
    success = print_result(*validate_file(path, partial="--partial" in sys.argv))
    sys.exit(0 if success else 1)