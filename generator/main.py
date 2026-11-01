import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from openpyxl import Workbook
from config import SEED, SHEETS, HEADERS, case_id
from crates import gen_crates
from network import gen_network
from radio import gen_radio
from windows import gen_windows
from incidents import gen_incidents
from sites import gen_sites
from chains import gen_chains
from sensors import gen_sensors
from safety import gen_safety
from rations import gen_rations
from traps import (trap_crates_46, trap_crates_47,
                   trap_network_48, trap_radio_49)

def build_case(k):
    rng = random.Random(f"{SEED}-{k}")
    cid = case_id(k)
    tables = {s: [] for s in SHEETS}
    capacity = None
    if k == 46:
        crates = trap_crates_46(rng, cid)
    elif k == 47:
        crates, capacity = trap_crates_47(rng, cid)
    else:
        crates = gen_crates(k, rng, cid)
    tables["crates"] = crates

    net = trap_network_48(rng, cid) if k == 48 else gen_network(k, rng, cid)
    tables["locations"] = net["locations"]
    tables["roads"] = net["roads"]
    tables["waves"] = net["waves"]
    rad = trap_radio_49(rng, cid) if k == 49 else gen_radio(k, rng, cid)
    tables["radio_log"] = rad["radio_log"]
    tables["radio_patterns"] = rad["radio_patterns"]
    tables["radio_reports"] = rad["radio_reports"]
    tables["windows"] = gen_windows(k, rng, cid)
    tables["incidents"] = gen_incidents(k, rng, cid)
    st = gen_sites(k, rng, cid)
    tables["sites"] = st["sites"]
    tables["tour"] = st["tour"]
    ch = gen_chains(k, rng, cid)
    tables["pipeline_dims"] = ch["pipeline_dims"]
    tables["drum_prices"] = ch["drum_prices"]
    se = gen_sensors(k, rng, cid)
    tables["sensor_edges"] = se["sensor_edges"]
    tables["sensor_cover"] = se["sensor_cover"]
    sf = gen_safety(k, rng, cid)
    tables["safety_rules"] = sf["safety_rules"]
    tables["safety_planted"] = sf["safety_planted"]
    ra = gen_rations(k, rng, cid)
    tables["rations"] = ra["rations"]
    info = {"targets": net["targets"], "V": net["V"], "E": net["E"],
            "edit_bound": rad["edit_bound"], "tour_length": st["tour_length"],
            "sensor_nodes": se["sensor_nodes"], "sensor_k": se["sensor_k"],
            "safety_vars": sf["safety_vars"], "rations_target": ra["rations_target"],
            "capacity": capacity}
    return tables, info

def main(out="cases.xlsx"):
    all_tables = {s: [] for s in SHEETS}
    infos = {}
    for k in range(50):
        t, infos[k] = build_case(k)
        for s in SHEETS:
            all_tables[s].extend(t[s])
    wb = Workbook()
    wb.remove(wb.active)
    for s in SHEETS:
        ws = wb.create_sheet(s)
        ws.append(HEADERS[s])
        for row in all_tables[s]:
            ws.append(row)
    wb.save(out)
    print("wrote", out)

if __name__ == "__main__":
    main()