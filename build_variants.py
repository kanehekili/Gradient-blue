#!/usr/bin/env python3
"""
Build Gradient GTK theme with multiple accent/selection colors.

For each color this script produces:
  build/Gradient-blue-{color}-{version}.{release}.tar.gz   (light theme)
  build/Gradient-black-{color}-{version}.{release}.tar.gz  (dark theme)

Versions are read from GTK-3.22/build.properties and
GTK-3.22-dark/build.properties so they stay in sync with the ant builds.

Usage:
  python3 build_variants.py                   # build all colors
  python3 build_variants.py green teal        # build specific colors
  python3 build_variants.py --list            # show defined colors
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.resolve()

# ── Color definitions ──────────────────────────────────────────────────────────
# Each entry: (bg, fg, gtk2_dark_muted)
#
#  bg            main accent / selection background color
#  fg            foreground on selection (light, readable tint)
#  gtk2_dark     muted, desaturated variant used as GTK2 dark fallback
#
# Note: $barLolight in GTK4 SCSS is computed from $selected_bg_color via
# desaturate(darken(...)) — no per-color value needed here.
# ──────────────────────────────────────────────────────────────────────────────
COLORS = {
    "blue":   ("#282DDC", "#A1A4FF", "#434592"),
    "green":  ("#1A8C2B", "#8EFFA0", "#3A6E42"),
    "red":    ("#CC2020", "#FFB3B3", "#8C4545"),
    "purple": ("#7B2FBE", "#DEB3FF", "#6B4B8C"),
    "teal":   ("#007878", "#B3FFFF", "#3A7070"),
    "orange": ("#C45A00", "#FFD0A0", "#8C6030"),
}

# ── Source files that are patched per color then restored ─────────────────────
def _patched_files():
    return {
        "colors_scss":   REPO / "GTK4-SASS/gtk4/_colors.scss",
        "light_css":     REPO / "GTK-3.22/src/Gradient-blue-324.2/gtk-3.0/gtk-contained.css",
        "light_gtkrc":   REPO / "GTK-3.22/src/Gradient-blue-324.2/gtk-2.0/gtkrc",
        "dark_css":      REPO / "GTK-3.22-dark/src/Gradient-black/gtk-3.0/gtk-contained.css",
        "dark_gtkrc":    REPO / "GTK-3.22-dark/src/Gradient-black/gtk-2.0/gtkrc",
        "xfce_blue":     REPO / "xfwm4/Gradient-blue/xfce-notify-4.0/gtk.css",
        "xfce_blue_24":  REPO / "xfwm4/Gradient-blue-HiDPI24/xfce-notify-4.0/gtk.css",
        "xfce_blue_28":  REPO / "xfwm4/Gradient-blue-HiDPI28/xfce-notify-4.0/gtk.css",
        "xfce_black":    REPO / "xfwm4/Gradient-black/xfce-notify-4.0/gtk.css",
        "xfce_black_24": REPO / "xfwm4/Gradient-black-HiDPI24/xfce-notify-4.0/gtk.css",
        "xfce_black_28": REPO / "xfwm4/Gradient-black-HiDPI28/xfce-notify-4.0/gtk.css",
    }

def _save():
    return {k: v.read_text() for k, v in _patched_files().items()}

def _restore(originals):
    for k, text in originals.items():
        _patched_files()[k].write_text(text)

# ── File patching helpers ─────────────────────────────────────────────────────

def _sub(path, pattern, replacement):
    text = path.read_text()
    new, n = re.subn(pattern, replacement, text)
    if n == 0:
        print(f"  WARNING: pattern not found in {path.name}")
    path.write_text(new)

def patch_colors_scss(bg, fg):
    f = _patched_files()["colors_scss"]
    text = f.read_text()
    text = re.sub(r'(\$selected_fg_color\s*:).*?;', rf'\g<1> {fg};', text)
    text = re.sub(r'(\$selected_bg_color\s*:).*?;', rf'\g<1>{bg};',  text)
    f.write_text(text)

def patch_gtk3_css(key, bg):
    _sub(_patched_files()[key],
         r'(@define-color selected_bg_color\s+)#[0-9A-Fa-f]{6}(;)',
         rf'\g<1>{bg}\g<2>')

def patch_light_gtkrc(bg):
    _sub(_patched_files()["light_gtkrc"],
         r'(selected_bg_color:)#[0-9A-Fa-f]{6}',
         rf'\g<1>{bg}')

def patch_dark_gtkrc(bg, bg_muted):
    f = _patched_files()["dark_gtkrc"]
    text = f.read_text()
    replacements = [bg, bg_muted]
    idx = [0]
    def _one(m):
        val = replacements[idx[0]] if idx[0] < len(replacements) else m.group(2)
        idx[0] += 1
        return m.group(1) + val + m.group(3)
    f.write_text(re.sub(
        r'(gtk_color_scheme\s*=\s*"selected_bg_color:)(#[0-9A-Fa-f]{6})(")',
        _one, text))

def patch_xfce(key, bg):
    _sub(_patched_files()[key],
         r'(@define-color selected_xfce_bg_color\s+)#[0-9A-Fa-f]{6}(;)',
         rf'\g<1>{bg}\g<2>')

# ── SCSS compilation ──────────────────────────────────────────────────────────

def compile_scss():
    gtk4_src  = REPO / "GTK4-SASS/gtk4"
    cinn_src  = REPO / "GTK4-SASS/cinnamon"
    gtk4_out  = REPO / "GTK4-SASS/build/gtk4"
    cinn_out  = REPO / "GTK4-SASS/build/cinnamon"

    jobs = [
        (gtk4_src / "Default-light.scss",    gtk4_out / "GTK4-light.css"),
        (gtk4_src / "Default-dark.scss",     gtk4_out / "GTK4-dark.css"),
        (gtk4_src / "Default-lightHi.scss",  gtk4_out / "GTK4-lightHi.css"),
        (gtk4_src / "Default-darkHi.scss",   gtk4_out / "GTK4-darkHi.css"),
        (gtk4_src / "Default-lightUHi.scss", gtk4_out / "GTK4-lightUHi.css"),
        (gtk4_src / "Default-darkUHi.scss",  gtk4_out / "GTK4-darkUHi.css"),
        (cinn_src / "Default-light.scss",    cinn_out / "cinnamon-light.css"),
        (cinn_src / "Default-dark.scss",     cinn_out / "cinnamon-dark.css"),
    ]
    for src, out in jobs:
        r = subprocess.run(["sassc", "-t", "compact", str(src), str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ERROR sassc {src.name}:\n{r.stderr[:300]}")
            return False
    return True

# ── Ant packaging ─────────────────────────────────────────────────────────────

def _read_props(path):
    props = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()
    return props

def run_ant(work_dir, extra_props):
    args = ["ant"] + [f"-D{k}={v}" for k, v in extra_props.items()]
    r = subprocess.run(args, cwd=work_dir, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  ERROR ant in {Path(work_dir).name}:\n{(r.stdout+r.stderr)[-400:]}")
        return False
    return True

# ── Per-color build ───────────────────────────────────────────────────────────

def build_color(name, bg, fg, bg_muted,
                build_light=True, build_dark=True):
    light_props = _read_props(REPO / "GTK-3.22/build.properties")
    dark_props  = _read_props(REPO / "GTK-3.22-dark/build.properties")
    ver         = light_props.get("version", "48")
    rel         = light_props.get("pkgrelease", "1")
    dark_ver    = dark_props.get("GB_dark", ver)
    dark_rel    = dark_props.get("pkgrelease", rel)

    print(f"\n── {name.upper()} ({bg}) ──────────────────────────────────")

    print("  Patching source files...")
    patch_colors_scss(bg, fg)
    if build_light:
        patch_gtk3_css("light_css", bg)
        patch_light_gtkrc(bg)
        for key in ("xfce_blue", "xfce_blue_24", "xfce_blue_28"):
            patch_xfce(key, bg)
    if build_dark:
        patch_gtk3_css("dark_css", bg)
        patch_dark_gtkrc(bg, bg_muted)
        for key in ("xfce_black", "xfce_black_24", "xfce_black_28"):
            patch_xfce(key, bg)

    print("  Compiling SCSS...")
    if not compile_scss():
        return False

    pkg_light = f"{name}-{ver}"
    pkg_dark  = f"{name}-{dark_ver}"

    if build_light:
        print("  Packaging light theme...")
        if not run_ant(REPO / "GTK-3.22",
                       {"version": pkg_light, "pkgrelease": rel,
                        "build": "../build/Light"}):
            return False

    if build_dark:
        print("  Packaging dark theme...")
        if not run_ant(REPO / "GTK-3.22-dark",
                       {"GB_dark": pkg_dark, "pkgrelease": dark_rel,
                        "build": "../build/Dark"}):
            return False

    report = []
    if build_light:
        report.append(("Light", "Gradient-blue",  pkg_light, rel))
    if build_dark:
        report.append(("Dark",  "Gradient-black", pkg_dark,  dark_rel))
    for subdir, prefix, pkg, release in report:
        archive = REPO / "build" / subdir / f"{prefix}-{pkg}.{release}.tar.gz"
        if archive.exists():
            size = archive.stat().st_size // 1024
            print(f"  ✓  {archive.name}  ({size} KB)")
        else:
            print(f"  !  {archive.name} — not found")

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
    variant = parser.add_mutually_exclusive_group()
    variant.add_argument("--light", action="store_true",
                         help="Build light (Gradient-blue) packages only")
    variant.add_argument("--dark", action="store_true",
                         help="Build dark (Gradient-black) packages only")
    args = parser.parse_args()

    if args.list:
        for name, (bg, fg, *_) in COLORS.items():
            print(f"  {name:<10}  bg={bg}  fg={fg}")
        return

    build_light = not args.dark
    build_dark  = not args.light

    chosen = args.colors or list(COLORS)
    invalid = [c for c in chosen if c not in COLORS]
    if invalid:
        print(f"Unknown color(s): {', '.join(invalid)}")
        print(f"Available: {', '.join(COLORS)}")
        sys.exit(1)

    variant_label = "light only" if args.light else "dark only" if args.dark else "light + dark"
    print(f"Building {len(chosen)} color variant(s): {', '.join(chosen)}  [{variant_label}]")

    originals = _save()
    failed = []
    try:
        for name in chosen:
            bg, fg, muted = COLORS[name]
            try:
                if not build_color(name, bg, fg, muted,
                                   build_light=build_light, build_dark=build_dark):
                    failed.append(name)
            except Exception as e:
                print(f"  EXCEPTION: {e}")
                failed.append(name)
    finally:
        print("\nRestoring source files...")
        _restore(originals)

    print()
    if failed:
        print(f"Failed: {', '.join(failed)}")
        sys.exit(1)
    print(f"Done. Archives are in {REPO / 'build'}/")

if __name__ == "__main__":
    main()
