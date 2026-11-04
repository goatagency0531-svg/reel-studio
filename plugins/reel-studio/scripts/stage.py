#!/usr/bin/env python3
"""Set a reel's stage. Usage: python3 stage.py <slug> <stage> [note] [--workspace DIR]"""
import argparse

from common import reel_dir, set_stage, workspace

ap = argparse.ArgumentParser()
ap.add_argument("slug")
ap.add_argument("stage")
ap.add_argument("note", nargs="?", default="")
ap.add_argument("--workspace")
a = ap.parse_args()
set_stage(reel_dir(workspace(a.workspace), a.slug), a.stage, a.note)
print(f"OK {a.slug} -> {a.stage}")
