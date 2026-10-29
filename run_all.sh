#!/bin/bash
# Reproduce project #93 end to end (CPU only, $0).
set -e
cd "$(dirname "$0")"
python3 -m pytest tests/ -q
PYTHONPATH=src python3 -m probeid.run headtohead --seed 101 --out results/headtohead.jsonl
PYTHONPATH=src python3 -m probeid.run gate-study --seed 101 --out results/gate_study.jsonl
PYTHONPATH=src python3 -m probeid.run summarize --in results/headtohead.jsonl
sha256sum results/headtohead.jsonl
