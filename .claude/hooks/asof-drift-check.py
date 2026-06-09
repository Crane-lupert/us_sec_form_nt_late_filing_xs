"""SessionStart hook template — drift check for _vendored/asof.

Copy this to your research repo's `.claude/hooks/` and wire via .claude/settings.json:

    {
      "hooks": [
        {
          "matcher": "SessionStart",
          "command": "python .claude/hooks/asof-drift-check.py"
        }
      ]
    }

Behavior:
    - Exit 0 always (non-blocking — warning only)
    - Prints drift status to stdout (visible at session start)
    - Schema-breaking drift → still exit 0 but prints loud warning + sync command

Per launch-bootstrap-protocol Rule 8 (2026-06-05) — bootstrap-time vendored copy with
manual sync. This hook gives you observability without forcing auto-sync.

Dependencies: stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]  # .claude/hooks/<this> -> repo root
VENDORED_ROOT = REPO_ROOT / "_vendored" / "asof_manifest"
LOCK_PATH = VENDORED_ROOT / "_manifest.lock"
META_HARNESS_SOT = Path("D:/vscode/meta-harness/data/asof-manifest")
SUPPORTED_SCHEMA_VERSIONS = ("v1",)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not LOCK_PATH.exists():
        # Vendored layout not initialized — only warn if _vendored/ folder exists at all
        if VENDORED_ROOT.parent.exists():
            print(
                f"⚠ asof: vendored layout missing at {VENDORED_ROOT}. "
                f"Run: python D:/vscode/meta-harness/scripts/asof-vendored/sync.py {REPO_ROOT}"
            )
        return 0  # non-blocking

    try:
        with open(LOCK_PATH, "r", encoding="utf-8") as f:
            lock = json.load(f)
    except Exception as e:
        print(f"⚠ asof: cannot read lock {LOCK_PATH}: {e}")
        return 0

    vendored_schema = lock.get("schema_version")
    if vendored_schema not in SUPPORTED_SCHEMA_VERSIONS:
        print(
            f"⚠ asof SCHEMA BREAKING — vendored schema={vendored_schema!r}, "
            f"supported={SUPPORTED_SCHEMA_VERSIONS}. Re-bootstrap required."
        )
        return 0

    if not META_HARNESS_SOT.exists():
        # Meta-harness path not accessible from this session — skip drift check
        return 0

    drifted = []
    for fname, expected_hash in lock.get("files", {}).items():
        sot_file = META_HARNESS_SOT / fname
        if not sot_file.exists():
            continue
        live_hash = _sha256_file(sot_file)
        if live_hash != expected_hash:
            drifted.append(fname)

    age_days = None
    try:
        synced_at = lock.get("synced_at") or lock.get("bootstrapped_at")
        if synced_at:
            synced_dt = datetime.fromisoformat(synced_at.replace("Z", "+00:00"))
            age_days = (datetime.now(synced_dt.tzinfo) - synced_dt).days
    except Exception:
        pass

    if drifted:
        age_str = f" (sync age {age_days}d)" if age_days is not None else ""
        print(
            f"⚠ asof drift: {len(drifted)} files stale{age_str}: "
            f"{', '.join(drifted[:3])}{'...' if len(drifted) > 3 else ''}"
        )
        print(f"  Refresh: python D:/vscode/meta-harness/scripts/asof-vendored/sync.py {REPO_ROOT}")
    else:
        # In sync — print nothing on success (avoid noise in every session)
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
