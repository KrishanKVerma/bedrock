"""Did the injection actually fire?"""

import glob

from harness.runlog import load

latest = sorted(glob.glob("runs/quotes_login_form_*.json"))[-1]
d = load(latest)
print("file:", latest)
print("injected field:", d["injected"])
print("steps:", len(d["steps"]))
for s in d["steps"]:
    print(f"  {s['n']}. {s['action']} [{s['action_ref']}] — elements_seen={s['elements_seen']}")