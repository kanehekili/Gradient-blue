#!/usr/bin/env python3
"""
Build Gradient GTK theme with multiple accent/selection colors.

For each color this script produces:
  build/Light/Gradient-{color}-{version}.{release}.tar.gz
  build/Dark/Gradient-black-{color}-{version}.{release}.tar.gz

Versions are read from GTK-3.22/build.properties and
GTK-3.22-dark/build.properties.

Usage:
  python3 build_variants.py                   # build all colors
  python3 build_variants.py green teal        # build specific colors
  python3 build_variants.py --list            # show defined colors
  python3 build_variants.py --light blue      # light variant only
  python3 build_variants.py --dark blue       # dark variant only
"""

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tarfile as _tarfile
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
    "blue":      ("#282DDC", "#A1A4FF", "#434592"),
    "green":     ("#1A8C2B", "#8EFFA0", "#3A6E42"),
    "red":       ("#CC2020", "#FFB3B3", "#8C4545"),
    "purple":    ("#7B2FBE", "#DEB3FF", "#6B4B8C"),
    "teal":      ("#007878", "#B3FFFF", "#3A7070"),
    "orange":    ("#C45A00", "#FFD0A0", "#8C6030"),
    "turquoise": ("#32B0A3", "#E0FFFE", "#2E7070"),
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

# ── Build properties ──────────────────────────────────────────────────────────

def _read_props(path):
    props = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()
    return props

# ── Packaging helpers ──────────────────────────────────────────────────────────

# Light source paths
_GTK_BASE_L   = REPO / "GTK-3.22/src/Gradient-blue-324.2"
_GTK_HI24_L   = REPO / "GTK-3.22/src/Gradient-blue-HiDPI24"
_GTK_HI28_L   = REPO / "GTK-3.22/src/Gradient-blue-HiDPI28"
_META_L       = REPO / "metacity/Gradient-blue"
_META_HI24_L  = REPO / "metacity/Gradient-blueHiDPI24"
_META_HI28_L  = REPO / "metacity/Gradient-blueHiDPI28"
_XFWM_L       = REPO / "xfwm4/Gradient-blue"
_XFWM_HI24_L  = REPO / "xfwm4/Gradient-blue-HiDPI24"
_XFWM_HI28_L  = REPO / "xfwm4/Gradient-blue-HiDPI28"

# Dark source paths
_GTK_BASE_D   = REPO / "GTK-3.22-dark/src/Gradient-black"
_GTK_HI24_D   = REPO / "GTK-3.22-dark/src/Gradient-black-HiDPI24"
_GTK_HI28_D   = REPO / "GTK-3.22-dark/src/Gradient-black-HiDPI28"
_META_D       = REPO / "metacity/Gradient-black"
_META_HI24_D  = REPO / "metacity/Gradient-blackHiDPI24"
_META_HI28_D  = REPO / "metacity/Gradient-blackHiDPI28"
_XFWM_D       = REPO / "xfwm4/Gradient-black"
_XFWM_HI24_D  = REPO / "xfwm4/Gradient-black-HiDPI24"
_XFWM_HI28_D  = REPO / "xfwm4/Gradient-black-HiDPI28"

_CINNAMON_SRC  = REPO / "Cinnamon"
_CINNAMON_SCSS = REPO / "GTK4-SASS/cinnamon"
_MISC_SRC      = REPO / "Misc"

_GTK4_CSS = {
    "light":    REPO / "GTK4-SASS/build/gtk4/GTK4-light.css",
    "lightHi":  REPO / "GTK4-SASS/build/gtk4/GTK4-lightHi.css",
    "lightUHi": REPO / "GTK4-SASS/build/gtk4/GTK4-lightUHi.css",
    "dark":     REPO / "GTK4-SASS/build/gtk4/GTK4-dark.css",
    "darkHi":   REPO / "GTK4-SASS/build/gtk4/GTK4-darkHi.css",
    "darkUHi":  REPO / "GTK4-SASS/build/gtk4/GTK4-darkUHi.css",
}

_CINN_CSS = {
    "light": REPO / "GTK4-SASS/build/cinnamon/cinnamon-light.css",
    "dark":  REPO / "GTK4-SASS/build/cinnamon/cinnamon-dark.css",
}


def _copy_tree(src, dst, skip_rel=(), skip_dirs=()):
    src, dst = Path(src), Path(dst)
    skip_set     = set(skip_rel)
    skip_dir_set = set(skip_dirs)
    for root, dirs, files in os.walk(str(src)):
        root_path = Path(root)
        rel_root  = root_path.relative_to(src)
        if rel_root == Path("."):
            dirs[:] = [d for d in dirs if d not in skip_dir_set]
        for fname in files:
            fpath = root_path / fname
            if not fpath.exists():
                continue
            rel = str(rel_root / fname)
            if rel in skip_set:
                continue
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fpath, target)


def _copy_tree_filtered(src, dst, exclude_files=(), exclude_dirs=()):
    src, dst = Path(src), Path(dst)
    exclude_dir_set = set(exclude_dirs)
    for root, dirs, files in os.walk(str(src)):
        dirs[:] = [d for d in dirs if d not in exclude_dir_set]
        root_path = Path(root)
        rel_root  = root_path.relative_to(src)
        for fname in files:
            if any(fnmatch.fnmatch(fname, p) for p in exclude_files):
                continue
            target = dst / rel_root / fname
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root_path / fname, target)


def _copy_orbs(metacity_src, dest_csd):
    """Copy *-orb* files from metacity_src/metacity-1/ into dest_csd/."""
    src = Path(metacity_src) / "metacity-1"
    dst = Path(dest_csd)
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob("*-orb*"):
        shutil.copy2(f, dst / f.name)


def _write_index(index_src, dest_dir, token_value):
    """Copy index.theme replacing @xxxx@ with token_value."""
    text = Path(index_src).read_text().replace("@xxxx@", token_value)
    (Path(dest_dir) / "index.theme").write_text(text)


def _build_variant_dir(dest, gtk_base, gtk_hi, metacity_src, xfwm_src,
                        gtk4_key, cinn_key, cinn_excl_dir,
                        base_skip, index_src, token_value):
    """Assemble one DPI variant directory, mirroring the Ant build steps."""
    dest = Path(dest)
    # 1. GTK base (colour-patched files already on disk)
    _copy_tree(gtk_base, dest, skip_rel=base_skip)
    # 2. HiDPI GTK overrides
    if gtk_hi:
        _copy_tree(gtk_hi, dest)
    # 3. Metacity theme
    _copy_tree(metacity_src, dest)
    # 4. xfwm4 theme
    _copy_tree(xfwm_src, dest)
    # 5. Cinnamon thumbnails
    _copy_tree(_CINNAMON_SRC, dest)
    # 6. Cinnamon compiled CSS
    (dest / "cinnamon").mkdir(parents=True, exist_ok=True)
    shutil.copy2(_CINN_CSS[cinn_key], dest / "cinnamon" / "cinnamon.css")
    # 7. Cinnamon assets (exclude opposite-variant assets)
    _copy_tree_filtered(_CINNAMON_SCSS, dest / "cinnamon",
                        exclude_files=("*.scss", "meson.build"),
                        exclude_dirs=(cinn_excl_dir,))
    # 8. Misc files
    _copy_tree_filtered(_MISC_SRC, dest, exclude_files=("*.sh",))
    # 9. GTK4 CSS
    gtk4_target = dest / "gtk-4.0" / "gtk4.css"
    gtk4_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_GTK4_CSS[gtk4_key], gtk4_target)
    # 10. CSD orb images
    _copy_orbs(metacity_src, dest / "csd")
    # 11. index.theme with token substitution (overwrites any copied earlier)
    _write_index(index_src, dest, token_value)


def _package_light_python(name, ver, rel, out_dir):
    """Build and archive the light (Gradient-blue) theme in pure Python."""
    out_dir = Path(out_dir)
    stage   = out_dir / "stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    # (theme_name, gtk_hi, metacity, xfwm, gtk4_key, index_dir, extra_base_skip)
    variants = [
        (f"Gradient-{name}-{ver}",
         None, _META_L, _XFWM_L, "light", _GTK_BASE_L, []),
        (f"Gradient-{name}-DPI24-{ver}",
         _GTK_HI24_L, _META_HI24_L, _XFWM_HI24_L, "lightHi", _GTK_HI24_L,
         ["gtk-3.0/gtk-decorations.css"]),
        (f"Gradient-{name}-DPI28-{ver}",
         _GTK_HI28_L, _META_HI28_L, _XFWM_HI28_L, "lightUHi", _GTK_HI28_L,
         ["gtk-3.0/gtk-decorations.css"]),
    ]

    theme_names = []
    for theme_name, gtk_hi, meta, xfwm, gtk4_key, index_dir, extra_skip in variants:
        theme_names.append(theme_name)
        dest = stage / theme_name
        dest.mkdir(parents=True, exist_ok=True)
        _build_variant_dir(
            dest=dest,
            gtk_base=_GTK_BASE_L,
            gtk_hi=gtk_hi,
            metacity_src=meta,
            xfwm_src=xfwm,
            gtk4_key=gtk4_key,
            cinn_key="light",
            cinn_excl_dir="dark-assets",
            base_skip=["index.theme"] + extra_skip,
            index_src=index_dir / "index.theme",
            token_value=theme_name,
        )

    for old in out_dir.glob(f"Gradient-{name}-{ver}*.tar.gz"):
        old.unlink()
    archive = out_dir / f"Gradient-{name}-{ver}.{rel}.tar.gz"
    with _tarfile.open(archive, "w:gz") as tar:
        for theme_name in theme_names:
            tar.add(stage / theme_name, arcname=theme_name)
    shutil.rmtree(stage)
    size = archive.stat().st_size // 1024
    print(f"  ✓  {archive.name}  ({size} KB)")
    return archive


def _package_dark_python(name, dark_ver, dark_rel, out_dir):
    """Build and archive the dark (Gradient-black) theme in pure Python."""
    out_dir  = Path(out_dir)
    pkg_dark = f"{name}-{dark_ver}"
    stage    = out_dir / "stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    variants = [
        (f"Gradient-black-{pkg_dark}",
         None, _META_D, _XFWM_D, "dark", _GTK_BASE_D, []),
        (f"Gradient-black-DPI24-{pkg_dark}",
         _GTK_HI24_D, _META_HI24_D, _XFWM_HI24_D, "darkHi", _GTK_HI24_D,
         ["gtk-3.0/gtk-decorations.css"]),
        (f"Gradient-black-DPI28-{pkg_dark}",
         _GTK_HI28_D, _META_HI28_D, _XFWM_HI28_D, "darkUHi", _GTK_HI28_D,
         ["gtk-3.0/gtk-decorations.css"]),
    ]

    theme_names = []
    for theme_name, gtk_hi, meta, xfwm, gtk4_key, index_dir, extra_skip in variants:
        theme_names.append(theme_name)
        dest = stage / theme_name
        dest.mkdir(parents=True, exist_ok=True)
        _build_variant_dir(
            dest=dest,
            gtk_base=_GTK_BASE_D,
            gtk_hi=gtk_hi,
            metacity_src=meta,
            xfwm_src=xfwm,
            gtk4_key=gtk4_key,
            cinn_key="dark",
            cinn_excl_dir="light-assets",
            base_skip=["index.theme"] + extra_skip,
            index_src=index_dir / "index.theme",
            token_value=pkg_dark,
        )

    for old in out_dir.glob(f"Gradient-black-{pkg_dark}*.tar.gz"):
        old.unlink()
    archive = out_dir / f"Gradient-black-{pkg_dark}.{dark_rel}.tar.gz"
    with _tarfile.open(archive, "w:gz") as tar:
        for theme_name in theme_names:
            tar.add(stage / theme_name, arcname=theme_name)
    shutil.rmtree(stage)
    size = archive.stat().st_size // 1024
    print(f"  ✓  {archive.name}  ({size} KB)")
    return archive


# ── Per-color build ───────────────────────────────────────────────────────────

def build_color(name, bg, fg, bg_muted, build_light=True, build_dark=True):
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

    print("  Packaging...")
    (REPO / "build/Light").mkdir(parents=True, exist_ok=True)
    (REPO / "build/Dark").mkdir(parents=True, exist_ok=True)
    if build_light:
        _package_light_python(name, ver, rel, REPO / "build/Light")
    if build_dark:
        _package_dark_python(name, dark_ver, dark_rel, REPO / "build/Dark")
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
            print(f"  {name:<12}  bg={bg}  fg={fg}")
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
                                   build_light=build_light,
                                   build_dark=build_dark):
                    failed.append(name)
            except Exception as e:
                print(f"  EXCEPTION: {e}")
                import traceback; traceback.print_exc()
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
