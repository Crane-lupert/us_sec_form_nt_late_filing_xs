# V5 Phase 0 step 3 — Lock F §8 grep result

**Date**: 2026-06-10
**Repo**: us_sec_form_nt_late_filing_xs
**Script**: `D:/vscode/meta-harness/scripts/audit-pipeline-determinism.sh`
**Verdict**: CLEAN (0 hits across all 4 anti-pattern signatures)

## §1 Result (verbatim script output)

```
==========================================================
Lock F — Pipeline Determinism Audit
Repo: d:/vscode/us_sec_form_nt_late_filing_xs
Search paths: d:/vscode/us_sec_form_nt_late_filing_xs/src d:/vscode/us_sec_form_nt_late_filing_xs/scripts
==========================================================

--- Pattern A — SQL ANY_VALUE() (CRITICAL) ---
(no hits)

--- Pattern A' — pandas groupby.agg(...first) on classification (HIGH) ---
(no hits)

--- Pattern B — drop_duplicates() (verify preceding sort_values) ---
(no hits)

--- Pattern C — agg("last"/"first") / .nth() (verify preceding sort_values) ---
(no hits)

==========================================================
RESULT: CLEAN (no signature anti-patterns matched)
==========================================================
```

## §2 Context

Phase 0 bootstrap state — `src/` contains only `__init__.py` (0 bytes); `scripts/` is empty.
Lock F clean is structural at this point. **Re-run obligation**: after every commit that adds Python code to `src/` or `scripts/`, the grep MUST run again (Phase 0 step 4 EDGAR pull, step 5 event-CAR, step 6 LLM classification, step 7 recurring-filer XS portfolio all add code).

## §3 V5-11(a) (data-validity tier 1) interaction

V5-11(a) requires: Lock F clean **AND** EDGAR Form NT bulk pull working **AND** NT-firm CIK match ≥90%.
- Lock F clean: **PASS** (this audit)
- EDGAR Form NT bulk pull: pending Phase 0 step 4
- CIK match ≥90%: pending Phase 0 step 4

## §4 Re-run cadence (locked)

| Trigger | Action |
|---|---|
| Pre-commit: any change to `src/`, `scripts/`, `research/` Python | run Lock F grep; abort commit if hit |
| Phase 0 step 4 end | run Lock F grep + commit result audit |
| Phase 0 step 6 end | run Lock F grep + commit result audit |
| Phase 0 step 7 end | run Lock F grep + commit result audit |
| V5-11(a) verdict commit | final Lock F grep + commit result audit |

Optionally wire as `.claude/hooks/PreToolUse` for `Edit`/`Write` matching `src/**.py` or `scripts/**.py` — deferred (not blocking).

## §5 Cross-reference
- Lock F origin: `D:/vscode/meta-harness/audits/2026-05-27-wrds-courier-pipeline-nondeterminism-discovery.md`
- Pipeline determinism test template: `D:/vscode/meta-harness/templates/pipeline-determinism-test.py.template`
