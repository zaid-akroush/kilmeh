# Result file format (`--jsonl`)

`kilmeh summarize-run <jobs_dir> --jsonl out.jsonl` writes one JSON object per trial (UTF-8, one line each). Nothing is written if the token-leak scan trips. Current `schema_version`: **1**. A change to field names or meaning bumps it.

| field | meaning |
|---|---|
| `schema_version` | integer, see above |
| `task_id`, `prompt_variant` | `task_name` split at `--` (`loop-for-to-while--levantine`); variant is null if there is no `--` |
| `agent`, `model` | from `agent_info` in `result.json` |
| `trial_id` | Harbor trial name |
| `reward` | float from `verifier/reward.txt`; null if missing |
| `status` | `passed` (reward >= 1), `failed`, `timeout` (`AgentTimeoutError`, reward kept), `error` (Harbor exception and no reward) |
| `checks` | `verifier/checks.json` as `{check: bool}`; null if the grader wrote none |
| `input_tokens`, `cached_tokens`, `output_tokens`, `cost_usd` | from `agent_result` in `result.json`, else `final_metrics` in the trajectory, else null |
| `duration_sec` | `finished_at - started_at` of the trial (includes setup and verifier) |
| `transcript` | path to `agent/trajectory.json` relative to the jobs dir; null if absent |
| `verify_log` | path to `verifier/verify.log`, relative; null if absent |
| `failure_cause` | null for a pass (`reward >= 1`); else `setup_timeout`, `agent_timeout`, `harness_error` or `tests_failed`, first match wins (see `summarize.py`) |
| `diff` | always null for now: Harbor 0.25 stores no diff (its `artifacts/` copy of `/logs/artifacts` is empty unless a task writes there) |

To count passes use `reward >= 1`, not `status == "passed"`: a `timeout` trial can keep reward 1.0 and the table counts it as passed.
