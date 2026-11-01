"""Build validator test copies and write validation_report.txt."""
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from openpyxl import Workbook, load_workbook
from config import HEADERS, SEED, SHEETS
from validate import print_result, validate_file

SRC = os.path.join(ROOT, "cases.xlsx")
TESTS = os.path.join(HERE, "tests")
REPORT = os.path.join(ROOT, "validation_report.txt")
BASE = [f"{SEED}-02", f"{SEED}-22"]

def extract(case_id):
    workbook = load_workbook(SRC, read_only=True)
    tables = {}
    for sheet in SHEETS:
        width = len(HEADERS[sheet])
        rows = workbook[sheet].iter_rows(values_only=True)
        header = list(next(rows))[:width]
        tables[sheet] = [header] + [list(row)[:width] for row in rows if row[0] == case_id]
    workbook.close()
    return tables

def write(tables, path):
    workbook = Workbook()
    workbook.remove(workbook.active)
    order = [sheet for sheet in SHEETS if sheet in tables] + [sheet for sheet in tables if sheet not in SHEETS]
    for sheet in order:
        worksheet = workbook.create_sheet(sheet)
        for row in tables[sheet]:
            worksheet.append(row)
    workbook.save(path)

def column(sheet, name):
    return HEADERS[sheet].index(name)

def case_id(tables):
    return tables["cases"][1][0]

def m_bad_header(t):
    t["crates"][0][column("crates", "weight")] = "weight_kg"

def m_extra_sheet(t):
    t["notes"] = [["case_id", "note"], [case_id(t), "hello"]]

def m_float_cell(t):
    t["crates"][1][column("crates", "weight")] = 7.5

def m_text_number(t):
    t["crates"][1][column("crates", "value")] = "55"

def m_empty_row(t):
    t["crates"].insert(2, [None] * len(HEADERS["crates"]))

def m_unsorted(t):
    t["crates"][1], t["crates"][2] = t["crates"][2], t["crates"][1]

def m_wrong_tier(t):
    index = column("cases", "tier")
    t["cases"][1][index] = "M" if t["cases"][1][index] == "S" else "S"

def m_no_case_row(t):
    t["cases"] = [t["cases"][0]]

def m_weight_zero(t):
    t["crates"][1][column("crates", "weight")] = 0

def m_dup_serial(t):
    index = column("crates", "serial")
    t["crates"][2][index] = t["crates"][1][index]

def m_capacity_high(t):
    weight = column("crates", "weight")
    t["cases"][1][column("cases", "capacity")] = sum(row[weight] for row in t["crates"][1:])

def m_bad_penalty(t):
    t["locations"][2][column("locations", "penalty")] = 3

def m_hq_wrong(t):
    t["locations"][1][column("locations", "type")] = "J"

def m_road_missing_end(t):
    t["roads"][1][column("roads", "v")] = len(t["locations"]) + 4

def m_road_repeat(t):
    u, v = column("roads", "u"), column("roads", "v")
    t["roads"][2][u], t["roads"][2][v] = t["roads"][1][u], t["roads"][1][v]

def m_waves_overlap(t):
    wave, road = column("waves", "wave_no"), column("waves", "road_no")
    rows = t["waves"][1:]
    t["waves"].append([case_id(t), max(row[wave] for row in rows) + 1, rows[0][road]])

def m_two_waves(t):
    wave = column("waves", "wave_no")
    before = len(t["waves"])
    t["waves"] = [t["waves"][0]] + [row for row in t["waves"][1:] if row[wave] < 2]
    return len(t["waves"]) != before

def m_pattern_count(t):
    t["radio_patterns"][1][column("radio_patterns", "count")] += 1

def m_bad_symbol(t):
    index = column("radio_log", "text")
    t["radio_log"][1][index] = "a" + t["radio_log"][1][index][1:]

def m_edit_bound_low(t):
    t["cases"][1][column("cases", "edit_bound")] = 0

def m_window_flat(t):
    window = t["windows"][1]
    window[column("windows", "finish")] = window[column("windows", "start")]

def m_ticks_decrease(t):
    index = column("incidents", "tick")
    if t["incidents"][-1][index] == 0:
        return False
    t["incidents"][-1][index] = 0

def m_tour_dup(t):
    index = column("tour", "site_no")
    t["tour"][2][index] = t["tour"][1][index]

def m_tour_length(t):
    t["cases"][1][column("cases", "tour_length")] += 1

def m_cover_missing(t):
    del t["sensor_cover"][1]

def m_safety_rule_broken(t):
    literals = t["safety_rules"][1][2:5]
    required = {abs(literal): (0 if literal > 0 else 1) for literal in literals}
    switch, value = column("safety_planted", "switch"), column("safety_planted", "value")
    for row in t["safety_planted"][1:]:
        if row[switch] in required:
            row[value] = required[row[switch]]

def m_ration_sum(t):
    planted, value = column("rations", "planted"), column("rations", "value")
    for row in t["rations"][1:]:
        if row[planted] == 1:
            row[value] += 1
            return True
    return False

def m_claim_wrong(t):
    if len(t["claims"]) < 2:
        return False
    t["claims"][1][column("claims", "cargo_opt")] += 1

MUTATIONS = [
    ("bad_header", m_bad_header, "a column header renamed", "V1"),
    ("extra_sheet", m_extra_sheet, "an extra sheet added", "V1"),
    ("float_cell", m_float_cell, "a float in an integer column", "V1"),
    ("text_number", m_text_number, "a number stored as text", "V1"),
    ("empty_row", m_empty_row, "an empty row inside a sheet", "V1"),
    ("unsorted", m_unsorted, "two crate rows out of order", "V1"),
    ("wrong_tier", m_wrong_tier, "wrong tier in the cases row", "V1"),
    ("no_case_row", m_no_case_row, "the cases row removed", "V1"),
    ("weight_zero", m_weight_zero, "a crate weight of 0", "V2"),
    ("dup_serial", m_dup_serial, "two crates with the same serial", "V2"),
    ("capacity_high", m_capacity_high, "capacity equals total weight", "V2"),
    ("bad_penalty", m_bad_penalty, "an invalid location penalty", "V2"),
    ("window_flat", m_window_flat, "a window with start equal to finish", "V2"),
    ("ticks_decrease", m_ticks_decrease, "alarm ticks that decrease", "V2"),
    ("hq_wrong", m_hq_wrong, "location 0 is not a depot", "V3"),
    ("road_missing_end", m_road_missing_end, "a road endpoint does not exist", "V3"),
    ("road_repeat", m_road_repeat, "the same road pair listed twice", "V3"),
    ("waves_overlap", m_waves_overlap, "one road in two waves", "V4"),
    ("pattern_count", m_pattern_count, "a radio pattern count is wrong", "V5"),
    ("bad_symbol", m_bad_symbol, "a lowercase radio symbol", "V5"),
    ("edit_bound_low", m_edit_bound_low, "edit_bound below the true distance", "V5"),
    ("claim_wrong", m_claim_wrong, "a Tier S claim is wrong", "V5"),
    ("tour_dup", m_tour_dup, "a site is visited twice", "V6"),
    ("tour_length", m_tour_length, "tour_length is wrong", "V6"),
    ("cover_missing", m_cover_missing, "a node is removed from the sensor cover", "V6"),
    ("safety_broken", m_safety_rule_broken, "a planted safety rule is broken", "V6"),
    ("ration_sum", m_ration_sum, "planted rations no longer sum to target", "V6"),
    ("two_waves", m_two_waves, "only two waves remain", "V7"),
]

def all_errors(path):
    global_errors, results = validate_file(path, partial=True)
    return global_errors + [error for errors in results.values() for error in errors]

def main():
    os.makedirs(TESTS, exist_ok=True)
    for filename in os.listdir(TESTS):
        if filename.endswith(".xlsx"):
            os.remove(os.path.join(TESTS, filename))
    problems, valid_records, broken_records = [], [], []
    for base_case in BASE:
        original = extract(base_case)
        valid_name = f"valid_{base_case}.xlsx"
        valid_path = os.path.join(TESTS, valid_name)
        write(original, valid_path)
        errors = all_errors(valid_path)
        valid_records.append((valid_name, errors))
        if errors:
            problems.append(f"valid copy {valid_name} was rejected: {errors[:2]}")
        for tag, mutation, description, expected_code in MUTATIONS:
            test = copy.deepcopy(original)
            if mutation(test) is False:
                continue
            filename = f"{base_case}__{tag}.xlsx"
            path = os.path.join(TESTS, filename)
            write(test, path)
            errors = all_errors(path)
            broken_records.append((base_case, filename, description, expected_code, errors))
            if not errors:
                problems.append(f"{filename} was ACCEPTED (should fail {expected_code})")
            elif not any(error.startswith(expected_code) for error in errors):
                problems.append(f"{filename}: rejected by the wrong check: {errors[:2]}")

    with open(REPORT, "w", encoding="utf-8") as report:
        report.write(f"VALIDATION REPORT (group seed {SEED})\n\n")
        report.write("=" * 70 + "\nPART 1: validator on cases.xlsx (all 50 cases)\n" + "=" * 70 + "\n")
        full_ok = print_result(*validate_file(SRC), out=report)
        report.write("\n" + "=" * 70 + "\nPART 2: valid test cases\n" + "=" * 70 + "\n")
        for filename, errors in valid_records:
            report.write(f"{filename}: {'PASS' if not errors else 'FAIL'}\n")
        report.write("\n" + "=" * 70 + "\nPART 3: broken copies\n" + "=" * 70 + "\n")
        for base_case in BASE:
            records = [record for record in broken_records if record[0] == base_case]
            report.write(f"\nBase case {base_case}: {len(records)} broken copies, {sum(bool(record[4]) for record in records)} rejected\n")
            for _, filename, description, expected_code, errors in records:
                report.write(f"  {filename}\n    defect : {description}\n    result : {'REJECTED' if errors else 'ACCEPTED (BUG)'} (expected {expected_code})\n")
                for error in errors[:3]:
                    report.write(f"      {error[:150]}\n")
        total = len(broken_records)
        rejected = sum(bool(record[4]) for record in broken_records)
        report.write(f"\nSUMMARY: {rejected}/{total} broken copies rejected; cases.xlsx {'PASS' if full_ok else 'FAIL'}\n")

    print(f"valid copies: {sum(not errors for _, errors in valid_records)}/{len(valid_records)} pass")
    print(f"broken copies: {sum(bool(record[4]) for record in broken_records)}/{len(broken_records)} rejected")
    for problem in problems:
        print("PROBLEM:", problem)
    print("report written to", REPORT)
    sys.exit(1 if problems or not full_ok else 0)

if __name__ == "__main__":
    main()