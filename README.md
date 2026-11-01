# LIFELINE: Algorithmic Relief-Command Engine

DAA semester project, FAST-NUCES Islamabad (BS Data Science and AI).
Group 69: Muhammad Umar (22I-0644), Haider Ali (22I-0502), Awwab Ahmed (23I-0079), all Section AI-A.

## Status
- Iteration 1 (data and algorithm selection): complete
- Iteration 2 (implementation and evaluation): in progress

## Setup
    pip install -r requirements.txt

## Iteration 1: reproduce and validate the data
    python generator/main.py                 # writes cases.xlsx (50 cases, 20 sheets, seed 69)
    python validator/validate.py cases.xlsx  # checks every case, prints PASS or the broken rules
    python validator/run_all.py              # broken-copy tests and validation_report.txt

## Folder layout
| Path | Contents |
|---|---|
| `config.py` | Shared constants (sheets, headers, tier ranges, seed) |
| `generator/` | Data generator (see its README) |
| `validator/` | Validator and `tests/` with broken copies |
| `cases.xlsx` | The 50 generated cases |
| `validation_report.txt` | Validator output |
| `approach_note.pdf` | Iteration 1 approach note |
| `proposal.pdf` | Algorithm-selection report |

## Chosen modules for Iteration 2
A (Relief inventory), B (Route planning), C (Rescue scheduling), D (Emergency queue).
