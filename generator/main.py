import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from openpyxl import Workbook
from config import SEED, SHEETS, HEADERS, case_id
from crates import gen_crates
from network import gen_network

def build_case(k):
    rng = random.Random(f"{SEED}-{k}")
    cid = case_id(k)
    tables = {s: [] for s in SHEETS}
    tables["crates"] = gen_crates(k, rng, cid)
    net = gen_network(k, rng, cid)
    tables["locations"] = net["locations"]
    tables["roads"] = net["roads"]
    tables["waves"] = net["waves"]
    info = {"targets": net["targets"], "V": net["V"], "E": net["E"]}
    return tables, info

def main(out="cases.xlsx"):
    all_tables = {s: [] for s in SHEETS}
    infos = {}
    for k in range(46):                      # traps 46-49 come later
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