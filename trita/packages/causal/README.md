# trita-causal

Association (F-CAUSAL-001), refutation battery (F-CAUSAL-002), card enrich (F-CAUSAL-003).

- `POST /v1/causal/run` — persist `analytics.causal_edges`
- Emitter auto-enriches cards when package is on `PYTHONPATH`
- L3 only when `refutation_status=pass` (VA-18; DB CHECK + `labels.l3_label`)

Gate: `python scripts/complete_rm3_gate.py` then `python scripts/verify_rm3_gate.py`
