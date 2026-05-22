# trita-proactive

Proactive triggers and digests (F-PROACTIVE-001..004).

| Trigger | ID |
|---------|-----|
| Cover below lead time | TR-COVER |
| Velocity down >40% | TR-VEL-DELTA |
| Causal L2/L3 promoted | TR-CAUSAL |
| Connector stale | TR-SYNC-FAIL |

API: `GET /v1/proactive/feed`, `POST /v1/proactive/run-triggers`, `POST /v1/proactive/digest/weekly`

Script: `python scripts/run_proactive_triggers.py`
