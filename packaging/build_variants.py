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
import shutil
import sys
import tarfile as _tarfile
from pathlib import Path

from build_engine import (
    REPO, GTK4_CSS, CINN_CSS,
    save, restore,
    patch_colors_scss, patch_light, patch_dark,
    compile_scss, read_props,
    copy_tree, copy_tree_filtered, copy_orbs, write_index,
)
from theme_colors import COLORS

# ── Source paths ──────────────────────────────────────────────────────────────

_GTK_BASE_L   = REPO / "GTK-3.22/src/Gradient-blue-324.2"
_GTK_HI24_L   = REPO / "GTK-3.22/src/Gradient-blue-HiDPI24"
_GTK_HI28_L   = REPO / "GTK-3.22/src/Gradient-blue-HiDPI28"
_META_L       = REPO / "metacity/Gradient-blue"
_META_HI24_L  = REPO / "metacity/Gradient-blueHiDPI24"
_META_HI28_L  = REPO / "metacity/Gradient-blueHiDPI28"
_XFWM_L       = REPO / "xfwm4/Gradient-blue"
_XFWM_HI24_L  = REPO / "xfwm4/Gradient-blue-HiDPI24"
_XFWM_HI28_L  = REPO / "xfwm4/Gradient-blue-HiDPI28"

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


# ── Assembly ──────────────────────────────────────────────────────────────────

def _build_variant_dir(dest, gtk_base, gtk_hi, metacity_src, xfwm_src,
                        gtk4_key, cinn_key, cinn_excl_dir,
                        base_skip, index_src, token_value):
    dest = Path(dest)
    copy_tree(gtk_base, dest, skip_rel=base_skip)
    if gtk_hi:
        copy_tree(gtk_hi, dest)
    copy_tree(metacity_src, dest)
    copy_tree(xfwm_src, dest)
    copy_tree(_CINNAMON_SRC, dest)
    (dest / "cinnamon").mkdir(parents=True, exist_ok=True)
    shutil.copy2(CINN_CSS[cinn_key], dest / "cinnamon" / "cinnamon.css")
    copy_tree_filtered(_CINNAMON_SCSS, dest / "cinnamon",
                       exclude_files=("*.scss", "meson.build"),
                       exclude_dirs=(cinn_excl_dir,))
    copy_tree_filtered(_MISC_SRC, dest, exclude_files=("*.sh",))
    gtk4_target = dest / "gtk-4.0" / "gtk4.css"
    gtk4_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GTK4_CSS[gtk4_key], gtk4_target)
    copy_orbs(metacity_src, dest / "csd")
    write_index(index_src, dest, token_value)


# ── Packaging ─────────────────────────────────────────────────────────────────

def _package_light(name, ver, rel, out_dir):
    out_dir = Path(out_dir)
    stage   = out_dir / "stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

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
            dest=dest, gtk_base=_GTK_BASE_L, gtk_hi=gtk_hi,
            metacity_src=meta, xfwm_src=xfwm, gtk4_key=gtk4_key,
            cinn_key="light", cinn_excl_dir="dark-assets",
            base_skip=["index.theme"] + extra_skip,
            index_src=index_dir / "index.theme", token_value=theme_name,
        )

    for old in out_dir.glob(f"Gradient-{name}-{ver}*.tar.gz"):
        old.unlink()
    archive = out_dir / f"Gradient-{name}-{ver}.{rel}.tar.gz"
    with _tarfile.open(archive, "w:gz") as tar:
        for theme_name in theme_names:
            tar.add(stage / theme_name, arcname=theme_name)
    shutil.rmtree(stage)
    print(f"  ✓  {archive.name}  ({archive.stat().st_size // 1024} KB)")


def _package_dark(name, dark_ver, dark_rel, out_dir):
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
            dest=dest, gtk_base=_GTK_BASE_D, gtk_hi=gtk_hi,
            metacity_src=meta, xfwm_src=xfwm, gtk4_key=gtk4_key,
            cinn_key="dark", cinn_excl_dir="light-assets",
            base_skip=["index.theme"] + extra_skip,
            index_src=index_dir / "index.theme", token_value=pkg_dark,
        )

    for old in out_dir.glob(f"Gradient-black-{pkg_dark}*.tar.gz"):
        old.unlink()
    archive = out_dir / f"Gradient-black-{pkg_dark}.{dark_rel}.tar.gz"
    with _tarfile.open(archive, "w:gz") as tar:
        for theme_name in theme_names:
            tar.add(stage / theme_name, arcname=theme_name)
    shutil.rmtree(stage)
    print(f"  ✓  {archive.name}  ({archive.stat().st_size // 1024} KB)")


# ── Public packaging functions (called by build_all.py) ───────────────────────

def package_gradient_light(name):
    props = read_props(REPO / "GTK-3.22/build.properties")
    out_dir = REPO / "build/Light"
    out_dir.mkdir(parents=True, exist_ok=True)
    _package_light(name, props.get("version", "48"), props.get("pkgrelease", "1"), out_dir)

def package_gradient_dark(name):
    props = read_props(REPO / "GTK-3.22-dark/build.properties")
    out_dir = REPO / "build/Dark"
    out_dir.mkdir(parents=True, exist_ok=True)
    _package_dark(name, props.get("GB_dark", "48"), props.get("pkgrelease", "1"), out_dir)


# ── Standalone build (patch + compile + package) ──────────────────────────────

def build_color(name, bg, fg_light, fg_dark, build_light=True, build_dark=True):
    light_props = read_props(REPO / "GTK-3.22/build.properties")
    dark_props  = read_props(REPO / "GTK-3.22-dark/build.properties")

    print(f"\n── {name.upper()} ({bg}) ──────────────────────────────────")
    print("  Patching source files...")
    patch_colors_scss(bg, fg_light, fg_dark)
    if build_light:
        patch_light(bg, fg_light)
    if build_dark:
        patch_dark(bg, fg_dark)

    print("  Compiling SCSS...")
    if not compile_scss():
        return False

    print("  Packaging...")
    if build_light:
        package_gradient_light(name)
    if build_dark:
        package_gradient_dark(name)
    return True


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("colors", nargs="*", help="Colors to build (default: all)")
    parser.add_argument("--list", action="store_true", help="List available colors and exit")
    variant = parser.add_mutually_exclusive_group()
    variant.add_argument("--light", action="store_true", help="Light packages only")
    variant.add_argument("--dark",  action="store_true", help="Dark packages only")
    args = parser.parse_args()

    if args.list:
        for name, (bg, *_) in COLORS.items():
            print(f"  {name:<12}  bg={bg}")
        return

    build_light = not args.dark
    build_dark  = not args.light
    chosen = args.colors or list(COLORS)
    invalid = [c for c in chosen if c not in COLORS]
    if invalid:
        print(f"Unknown color(s): {', '.join(invalid)}")
        print(f"Available: {', '.join(COLORS)}")
        sys.exit(1)

    label = "light only" if args.light else "dark only" if args.dark else "light + dark"
    print(f"Building {len(chosen)} color(s): {', '.join(chosen)}  [{label}]")

    originals = save()
    failed = []
    try:
        for name in chosen:
            bg, fg_light, fg_dark = COLORS[name]
            try:
                if not build_color(name, bg, fg_light, fg_dark,
                                   build_light=build_light, build_dark=build_dark):
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
