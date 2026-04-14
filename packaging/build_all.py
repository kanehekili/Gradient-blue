#!/usr/bin/env python3
"""
Full Gradient-blue build: light, dark, and all decorator variants in one run.

Patches source files once per color, compiles SCSS once, then packages every
profile.  To add a new decorator: drop a JSON config into configs/ and add one
as_profile() line to PROFILES below — nothing else changes.

Usage:
  python3 build_all.py                   # build all colors
  python3 build_all.py green teal        # build specific colors
  python3 build_all.py --list            # list available colors
"""

import argparse
import sys
from pathlib import Path

_HERE = Path(__file__).parent.resolve()

from build_engine import (
    REPO,
    save, restore,
    patch_colors_scss, patch_light, patch_dark,
    compile_scss,
)
from build_variants import package_gradient_light, package_gradient_dark
import generate_theme
from theme_colors import COLORS


# ── Profiles ──────────────────────────────────────────────────────────────────
# Built-in Gradient variants come first; decorator configs follow.
# To add a new decorator: one new as_profile() line pointing at its config.

PROFILES = [
    {"label": "Gradient light", "variant": "light", "fn": package_gradient_light},
    {"label": "Gradient dark",  "variant": "dark",  "fn": package_gradient_dark},
    generate_theme.as_profile(generate_theme.load_config(_HERE / "configs/winshine.json")),
]


# ── Per-color build ───────────────────────────────────────────────────────────

def _build_color(name, bg, fg_light, fg_dark):
    needs_light = any(p["variant"] == "light" for p in PROFILES)
    needs_dark  = any(p["variant"] == "dark"  for p in PROFILES)

    print(f"\n── {name.upper()} ({bg}) ──────────────────────────────────")
    print("  Patching source files...")
    patch_colors_scss(bg, fg_light, fg_dark)
    if needs_light:
        patch_light(bg, fg_light)
    if needs_dark:
        patch_dark(bg, fg_dark)

    print("  Compiling SCSS...")
    if not compile_scss():
        return False

    print("  Packaging...")
    for profile in PROFILES:
        profile["fn"](name)
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("colors", nargs="*",
                        help="Colors to build (default: all)")
    parser.add_argument("--list", action="store_true",
                        help="List available colors and exit")
    args = parser.parse_args()

    if args.list:
        for name, (bg, *_) in COLORS.items():
            print(f"  {name:<12}  bg={bg}")
        return

    chosen = args.colors or list(COLORS)
    invalid = [c for c in chosen if c not in COLORS]
    if invalid:
        print(f"Unknown color(s): {', '.join(invalid)}")
        print(f"Available: {', '.join(COLORS)}")
        sys.exit(1)

    labels = ", ".join(p["label"] for p in PROFILES)
    print(f"Building {len(chosen)} color(s): {', '.join(chosen)}")
    print(f"Profiles: {labels}")

    originals = save()
    failed = []
    try:
        for name in chosen:
            bg, fg_light, fg_dark = COLORS[name]
            try:
                if not _build_color(name, bg, fg_light, fg_dark):
                    failed.append(name)
            except Exception as e:
                print(f"  EXCEPTION: {e}")
                import traceback; traceback.print_exc()
                failed.append(name)
    finally:
        print("\nRestoring source files...")
        restore(originals)

    print()
    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)
    print(f"Done. Archives are in {REPO / 'build'}/")


if __name__ == "__main__":
    main()
