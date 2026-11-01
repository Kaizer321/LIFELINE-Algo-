import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from openpyxl import load_workbook
from config import SHEETS, HEADERS

TEXT = {"case_id", "tier", "type", "text", "pattern", "report_a", "report_b"}
SHOW = 3

def load(path):
    """Return (data, errors), with data[sheet] containing row dictionaries."""
    errs, data = [], {}
    wb = load_workbook(path, read_only=True)
    if wb.sheetnames != SHEETS:
        errs.append(f"V1: sheets are {wb.sheetnames}, expected {SHEETS}")
    for sheet in SHEETS:
        if sheet not in wb.sheetnames:
            continue
        it = wb[sheet].iter_rows(values_only=True)
        header = list(next(it, ()))
        while header and header[-1] is None:
            header.pop()
        if header != HEADERS[sheet]:
            errs.append(f"V1: sheet {sheet}: header {header} != {HEADERS[sheet]}")
            continue
        rows, bad_count, previous = [], 0, None
        for row_number, raw in enumerate(it, start=2):
            raw = list(raw)
            extra, raw = raw[len(header):], raw[:len(header)]
            if all(value is None for value in raw + extra):
                bad_count += 1
                if bad_count <= SHOW:
                    errs.append(f"V1: sheet {sheet} row {row_number}: empty row")
                continue
            problems = []
            if any(value is not None for value in extra):
                problems.append("data outside the header columns")
            for name, value in zip(header, raw):
                if name in TEXT:
                    valid = isinstance(value, str) and value.isascii() and not value.startswith("=")
                else:
                    valid = isinstance(value, int) and not isinstance(value, bool)
                if not valid:
                    problems.append(f"{name}={value!r} has the wrong type or format")
            if problems:
                bad_count += 1
                if bad_count <= SHOW:
                    errs.append(f"V1: sheet {sheet} row {row_number}: {'; '.join(problems)}")
                continue
            row = dict(zip(header, raw))
            if len(header) > 1:
                key = (row[header[0]], row[header[1]])
                if previous is not None and key < previous:
                    bad_count += 1
                    if bad_count <= SHOW:
                        errs.append(f"V1: sheet {sheet} row {row_number}: rows not sorted by case_id then {header[1]}")
                previous = key
            rows.append(row)
        if bad_count > SHOW:
            errs.append(f"V1: sheet {sheet}: {bad_count - SHOW} more bad rows not shown")
        data[sheet] = rows
    wb.close()
    return data, errs