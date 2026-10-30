#!/usr/bin/env python3
"""Render every video/photo in a folder (default: inputs/) with its plan.

For each file  inputs/NAME.mp4 (or .mov/.jpg/.png ...) the plan is chosen in this order:
  inputs/NAME.json  ->  inputs/plan.json  ->  example_plan.json
Results go to outputs/NAME_effects.mp4

  python render_inputs.py                      # everything in inputs/
  python render_inputs.py path/to/file.mp4 --plan my_plan.json
"""
import argparse, glob, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# vox/vox.py = fx.py + 17 Vox effects, so every plan works with it
ENGINE = os.path.join(HERE, "vox", "vox.py") if os.path.exists(os.path.join(HERE, "vox", "vox.py")) else os.path.join(HERE, "fx.py")
MEDIA = (".mp4", ".mov", ".m4v", ".webm", ".mkv", ".jpg", ".jpeg", ".png", ".webp")

def pick_plan(path, explicit):
    if explicit: return explicit
    base = os.path.splitext(path)[0]
    for p in (base + ".json", os.path.join(os.path.dirname(path), "plan.json"), os.path.join(HERE, "example_plan.json")):
        if os.path.exists(p): return p
    sys.exit("No plan found")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", nargs="?", default=os.path.join(HERE, "inputs"))
    ap.add_argument("--plan"); ap.add_argument("--out", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--max-short", default="1080")
    a = ap.parse_args()
    files = [a.target] if os.path.isfile(a.target) else sorted(
        f for f in glob.glob(os.path.join(a.target, "*")) if f.lower().endswith(MEDIA) and "_clip." not in f)
    if not files:
        print(f"No videos/photos found in {a.target} - nothing to do"); return
    os.makedirs(a.out, exist_ok=True); ok = 0
    for f in files:
        plan = pick_plan(f, a.plan)
        out = os.path.join(a.out, os.path.splitext(os.path.basename(f))[0] + "_effects.mp4")
        print(f"==> {f}  (plan: {os.path.relpath(plan, HERE)})  ->  {os.path.relpath(out, HERE)}", flush=True)
        r = subprocess.run([sys.executable, ENGINE, f, out, "--plan", plan, "--max-short", str(a.max_short)])
        ok += r.returncode == 0
        clip = os.path.join(os.path.dirname(out), os.path.splitext(os.path.basename(f))[0] + "_clip.mp4")
        if os.path.exists(clip): os.remove(clip)
    print(f"Rendered {ok}/{len(files)}")
    sys.exit(0 if ok == len(files) else 1)

if __name__ == "__main__":
    main()
