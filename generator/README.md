# LIFELINE generator (group seed 69)

Writes `cases.xlsx` (50 cases, 20 sheets) from the group seed. All randomness comes from `random.Random("69-k")` for case k, so the same seed always gives the same data.

## Reproduce cases.xlsx (one command, run from the project root)

	python generator/main.py

Setup once: `pip install -r requirements.txt` (needs Python 3 and openpyxl).

## Then validate

	python validator/validate.py cases.xlsx
	python validator/run_all.py

## Conventions
- Waves, tour steps, pipeline idx and sensor nodes start at 0; radio parts, windows, alarms, rules and crates start at 1.
- Touching windows (one finishes when another starts) are compatible, and do not count as overlapping.
- Tour ties in the nearest-neighbour rule go to the lowest site number.
- Trap 49 uses a repeated block of length 1; "repetition" means agreement with the best block of at most 8 symbols.
