"""Manually log a completed sweep result into the cross-session distribution."""

import sys

from harness.session_log import SessionResult, append, summary

# usage: python -m tests.log_session <tag> <condition> <provider> <runs> <silent> <elements>
if len(sys.argv) == 7:
    _, tag, cond, prov, runs, silent, elems = sys.argv
    append(SessionResult(tag, cond, prov, int(runs), int(silent), int(elems)))
    print(f"logged: {tag} {cond} {silent}/{runs}")

print("\n" + summary())