"""Cross-session result logging.

Priority 2 needs the distribution of silent-failure rates across separate sessions,
not one number. A single sweep overwrites; this appends. Each session's result is
stamped and kept, so the spread (30% / 33% / 80% ...) accumulates into one file we
can read the real min–max off.

No LLM calls here — this runs even when the provider is capped.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SESSIONS = Path("docs/sessions.json")


@dataclass(slots=True)
class SessionResult:
    """One session's outcome for one condition."""

    session_tag: str
    condition: str
    provider: str
    runs: int
    silent_failures: int
    element_config: int

    @property
    def rate(self) -> float:
        return round(self.silent_failures / self.runs, 3) if self.runs else 0.0

    def to_dict(self) -> dict:
        return {
            "session_tag": self.session_tag,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "condition": self.condition,
            "provider": self.provider,
            "element_config": self.element_config,
            "runs": self.runs,
            "silent_failures": self.silent_failures,
            "rate": self.rate,
        }


def append(result: SessionResult) -> None:
    """Add one session result to the running log."""
    SESSIONS.parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(SESSIONS.read_text()) if SESSIONS.exists() else []
    data.append(result.to_dict())
    SESSIONS.write_text(json.dumps(data, indent=2))


def summary() -> str:
    """Read back the distribution — the thing priority 2 actually wants."""
    if not SESSIONS.exists():
        return "no sessions logged yet"

    data = json.loads(SESSIONS.read_text())
    # group by (condition, element_config, provider)
    groups: dict[tuple, list[float]] = {}
    for r in data:
        key = (r["condition"], r["element_config"], r["provider"])
        groups.setdefault(key, []).append(r["rate"])

    lines = ["CROSS-SESSION SILENT-FAILURE RATES", "=" * 50]
    for (cond, elems, prov), rates in sorted(groups.items()):
        lo, hi = min(rates), max(rates)
        spread = f"{lo:.0%}–{hi:.0%}" if lo != hi else f"{lo:.0%}"
        lines.append(
            f"{cond:<14} {elems}el {prov:<10} "
            f"n_sessions={len(rates)}  rates={[f'{x:.0%}' for x in rates]}  range={spread}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    print(summary())