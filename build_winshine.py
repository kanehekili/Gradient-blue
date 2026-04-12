#!/usr/bin/env python3
"""
Build WinShine-light GTK theme variants with 6 accent colors.

For each color this script produces:
  build/winshine-light/WinShine-{color}-{version}.{release}.tar.gz

The archive contains three theme folders:
  WinShine-{color}-{version}/          standard DPI
  WinShine-{color}-DPI24-{version}/    HiDPI 24 px
  WinShine-{color}-DPI28-{version}/    HiDPI 28 px

Each packages the Gradient-blue GTK theme with WinShine xfwm4 decorations,
WinShine metacity theme, CSD, and Cinnamon.  There is no dark variant.

Usage:
  python3 build_winshine.py                  # build all colors
  python3 build_winshine.py green teal       # build specific colors
  python3 build_winshine.py --list           # list available colors
"""

import argparse
import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).parent.resolve()

# ── Color definitions ──────────────────────────────────────────────────────────
# (bg, fg, _unused_dark_muted)  — same palette as build_variants.py
COLORS = {
    "blue":   ("#282DDC", "#A1A4FF", "#434592"),
    "green":  ("#1A8C2B", "#8EFFA0", "#3A6E42"),
    "red":    ("#CC2020", "#FFB3B3", "#8C4545"),
    "purple": ("#7B2FBE", "#DEB3FF", "#6B4B8C"),
    "teal":   ("#007878", "#B3FFFF", "#3A7070"),
    "orange":    ("#C45A00", "#FFD0A0", "#8C6030"),
    "turquoise": ("#32B0A3", "#E0FFFE", "#2E7070"),
}

# ── Fixed source paths ─────────────────────────────────────────────────────────

GTK_BASE      = REPO / "GTK-3.22/src/Gradient-blue-324.2"
GTK_HI24      = REPO / "GTK-3.22/src/Gradient-blue-HiDPI24"
GTK_HI28      = REPO / "GTK-3.22/src/Gradient-blue-HiDPI28"

XFCE_NOTIFY    = REPO / "xfwm4/Gradient-blue/xfce-notify-4.0"
XFCE_NOTIFY_24 = REPO / "xfwm4/Gradient-blue-HiDPI24/xfce-notify-4.0"
XFCE_NOTIFY_28 = REPO / "xfwm4/Gradient-blue-HiDPI28/xfce-notify-4.0"

WINSHINE_SRC   = REPO / "xfwm4/WinShine/src"

METACITY_WS     = REPO / "metacity/WinShine/metacity-1"
METACITY_WS_HI  = REPO / "metacity/WinShineHiDPI/metacity-1"
METACITY_WS_XHI = REPO / "metacity/WinShineXHiDPI/metacity-1"

CINNAMON_SRC   = REPO / "Cinnamon"
CINNAMON_SCSS  = REPO / "GTK4-SASS/cinnamon"
CINNAMON_CSS   = REPO / "GTK4-SASS/build/cinnamon/cinnamon-light.css"

MISC_SRC       = REPO / "Misc"

GTK4_LIGHT     = REPO / "GTK4-SASS/build/gtk4/GTK4-light.css"
GTK4_LIGHTHI   = REPO / "GTK4-SASS/build/gtk4/GTK4-lightHi.css"
GTK4_LIGHTUHI  = REPO / "GTK4-SASS/build/gtk4/GTK4-lightUHi.css"


# ── Source files patched per color (always restored) ──────────────────────────

def _patched_files():
    return {
        "colors_scss":  REPO / "GTK4-SASS/gtk4/_colors.scss",
        "light_css":    GTK_BASE / "gtk-3.0/gtk-contained.css",
        "light_gtkrc":  GTK_BASE / "gtk-2.0/gtkrc",
        "xfce_blue":    XFCE_NOTIFY    / "gtk.css",
        "xfce_blue_24": XFCE_NOTIFY_24 / "gtk.css",
        "xfce_blue_28": XFCE_NOTIFY_28 / "gtk.css",
    }

def _save():
    return {k: v.read_text() for k, v in _patched_files().items()}

def _restore(originals):
    for k, text in originals.items():
        _patched_files()[k].write_text(text)


# ── Patching helpers ───────────────────────────────────────────────────────────

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

def patch_gtk3_css(bg):
    _sub(_patched_files()["light_css"],
         r'(@define-color selected_bg_color\s+)#[0-9A-Fa-f]{6}(;)',
         rf'\g<1>{bg}\g<2>')

def patch_light_gtkrc(bg):
    _sub(_patched_files()["light_gtkrc"],
         r'(selected_bg_color:)#[0-9A-Fa-f]{6}',
         rf'\g<1>{bg}')

def patch_xfce(key, bg):
    _sub(_patched_files()[key],
         r'(@define-color selected_xfce_bg_color\s+)#[0-9A-Fa-f]{6}(;)',
         rf'\g<1>{bg}\g<2>')


# ── SCSS compilation (light GTK4 + Cinnamon) ──────────────────────────────────

def compile_scss():
    gtk4_src = REPO / "GTK4-SASS/gtk4"
    cinn_src = REPO / "GTK4-SASS/cinnamon"
    gtk4_out = REPO / "GTK4-SASS/build/gtk4"
    cinn_out = REPO / "GTK4-SASS/build/cinnamon"

    jobs = [
        (gtk4_src / "Default-light.scss",    gtk4_out / "GTK4-light.css"),
        (gtk4_src / "Default-lightHi.scss",  gtk4_out / "GTK4-lightHi.css"),
        (gtk4_src / "Default-lightUHi.scss", gtk4_out / "GTK4-lightUHi.css"),
        (cinn_src / "Default-light.scss",    cinn_out / "cinnamon-light.css"),
    ]
    for src, out in jobs:
        r = subprocess.run(["sassc", "-t", "compact", str(src), str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ERROR sassc {src.name}:\n{r.stderr[:300]}")
            return False
    return True


# ── File copy helpers ──────────────────────────────────────────────────────────

def _copy_tree(src, dst, skip_rel=(), skip_dirs=()):
    """Copy src tree into dst using os.walk (no symlink following).

    skip_rel:  exact relative file paths to skip, e.g. "index.theme"
    skip_dirs: top-level directory names to skip entirely, e.g. "xfce-notify-4.0"
    """
    src, dst = Path(src), Path(dst)
    skip_set     = set(skip_rel)
    skip_dir_set = set(skip_dirs)

    for root, dirs, files in os.walk(str(src)):
        root_path = Path(root)
        rel_root  = root_path.relative_to(src)

        # Prune top-level dirs we want to skip (modifies dirs in-place)
        if rel_root == Path("."):
            dirs[:] = [d for d in dirs if d not in skip_dir_set]

        for fname in files:
            fpath = root_path / fname
            if not fpath.exists():   # skip broken symlinks
                continue
            rel = str(rel_root / fname)
            if rel in skip_set:
                continue
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fpath, target)


def _copy_tree_filtered(src, dst, exclude_files=(), exclude_dirs=()):
    """Copy src tree into dst, excluding files by glob and dirs by name."""
    src, dst = Path(src), Path(dst)
    exclude_dir_set = set(exclude_dirs)
    for root, dirs, files in os.walk(str(src)):
        # Prune excluded dirs in-place so os.walk won't descend into them
        dirs[:] = [d for d in dirs if d not in exclude_dir_set]
        root_path = Path(root)
        rel_root  = root_path.relative_to(src)
        for fname in files:
            if any(fnmatch.fnmatch(fname, p) for p in exclude_files):
                continue
            rel    = rel_root / fname
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root_path / fname, target)


# ── index.theme generation ─────────────────────────────────────────────────────

def _index_theme(theme_name):
    return (
        "[Desktop Entry]\n"
        "Type=X-GNOME-Metatheme\n"
        f"Name={theme_name}\n"
        "Comment=A gradient theme with WinShine decorations\n"
        "Encoding=UTF-8\n"
        "\n"
        "[X-GNOME-Metatheme]\n"
        f"GtkTheme={theme_name}\n"
        f"MetacityTheme={theme_name}\n"
        "IconTheme=elementary-xfce-dark\n"
        "CursorTheme=DMZ-White\n"
        "ButtonLayout=:minimize,maximize,close\n"
    )


# ── Button sizes per WinShine DPI (close_w, small_w, btn_h) ──────────────────
_WS_BTN_SIZES = {
    "WinShine":       (43, 24, 24),
    "WinShineHiDPI":  (64, 36, 34),
    "WinShineXHiDPI": (76, 42, 40),
}


def _gtk4_csd_block(csd_dir, ws_subdir):
    """Return CSS that overrides GTK4 windowcontrols button styles with WinShine images.

    Images are accessed via ../gtk-3.0/{csd_dir}/ (relative to gtk-4.0/gtk4.css).
    """
    close_w, small_w, btn_h = _WS_BTN_SIZES[ws_subdir]
    img = f"../gtk-3.0/{csd_dir}"
    lines = [
        "\n/* ── WinShine CSD overrides for GTK4 ────────────────────────── */",
        "windowcontrols button.minimize,",
        "windowcontrols button.maximize,",
        "windowcontrols button.close {",
        f"  min-height: {btn_h}px;",
        "  padding: 0; border: none; border-radius: 0;",
        "  color: transparent;",
        "  background-position: center; background-repeat: no-repeat; background-size: auto; }",
        f"windowcontrols button.close    {{ min-width: {close_w}px; }}",
        f"windowcontrols button.maximize {{ min-width: {small_w}px; }}",
        f"windowcontrols button.minimize {{ min-width: {small_w}px; }}",
        f'windowcontrols button.close         {{ background-image: url("{img}/button-close.png"); }}',
        f'windowcontrols button.close:hover   {{ background-image: url("{img}/button-close-hover.png"); }}',
        f'windowcontrols button.close:backdrop {{ background-image: url("{img}/button-close-inactive.png"); background-size: auto; }}',
        f'windowcontrols button.close:active  {{ background-image: url("{img}/button-close-focus.png"); }}',
        f'windowcontrols button.maximize         {{ background-image: url("{img}/button-max.png"); }}',
        f'windowcontrols button.maximize:hover   {{ background-image: url("{img}/button-max-hover.png"); }}',
        f'windowcontrols button.maximize:backdrop {{ background-image: url("{img}/button-max-inactive.png"); background-size: auto; }}',
        f'windowcontrols button.maximize:active  {{ background-image: url("{img}/button-max-focus.png"); }}',
        f'windowcontrols button.minimize         {{ background-image: url("{img}/button-min.png"); }}',
        f'windowcontrols button.minimize:hover   {{ background-image: url("{img}/button-min-hover.png"); }}',
        f'windowcontrols button.minimize:backdrop {{ background-image: url("{img}/button-min-inactive.png"); background-size: auto; }}',
        f'windowcontrols button.minimize:active  {{ background-image: url("{img}/button-min-focus.png"); }}',
    ]
    return "\n".join(lines) + "\n"


# ── DPI variant descriptors ────────────────────────────────────────────────────
# (theme_suffix, gtk_hi_src, winshine_subdir, notify_src, metacity_xml_src,
#  gtk4_css, base_skip, csd_css_name)

_VARIANTS = [
    ("",
     None,
     "WinShine",
     XFCE_NOTIFY,
     METACITY_WS,
     GTK4_LIGHT,
     ["index.theme"],
     "csd-winshine.css"),
    ("-DPI24",
     GTK_HI24,
     "WinShineHiDPI",
     XFCE_NOTIFY_24,
     METACITY_WS_HI,
     GTK4_LIGHTHI,
     ["index.theme", "gtk-3.0/gtk-decorations.css"],
     "csd-winshine-hidpi.css"),
    ("-DPI28",
     GTK_HI28,
     "WinShineXHiDPI",
     XFCE_NOTIFY_28,
     METACITY_WS_XHI,
     GTK4_LIGHTUHI,
     ["index.theme", "gtk-3.0/gtk-decorations.css"],
     "csd-winshine-xhidpi.css"),
]


# ── Per-theme-dir assembly ─────────────────────────────────────────────────────

def _build_theme_dir(dest, gtk_hi, ws_subdir, notify_src, metacity_xml_src,
                     gtk4_css, base_skip, csd_css_name):
    ws = WINSHINE_SRC / ws_subdir

    # 1. GTK base source (color-patched gtk-contained.css + gtkrc already on disk)
    _copy_tree(GTK_BASE, dest, skip_rel=base_skip)

    # 2. HiDPI GTK overrides (if any); index.theme generated separately,
    #    xfce-notify-4.0 always comes from the patched xfwm4 location (step 3)
    if gtk_hi:
        _copy_tree(gtk_hi, dest, skip_rel=["index.theme"],
                   skip_dirs=["xfce-notify-4.0"])

    # 3. xfce-notify (color-patched)
    _copy_tree(notify_src, dest / "xfce-notify-4.0")

    # 4. WinShine xfwm4 decoration
    _copy_tree(ws / "xfwm4", dest / "xfwm4")

    # 5. WinShine CSD — merge into gtk-3.0/ alongside existing GTK CSS
    _copy_tree(ws / "gtk-3.0", dest / "gtk-3.0")

    # 5b. Replace gtk-decorations.css (which references non-existent orb PNGs)
    #     with a simple import of the WinShine CSD stylesheet.
    (dest / "gtk-3.0" / "gtk-decorations.css").write_text(
        f'@import url("{csd_css_name}");\n'
    )

    # 6. WinShine metacity theme: XML from source + PNGs from xfwm4 images
    meta_dst = dest / "metacity-1"
    _copy_tree(metacity_xml_src, meta_dst)           # XML files
    _copy_tree_filtered(ws / "xfwm4", meta_dst,      # button/frame PNGs
                        exclude_files=("*.xpm", "themerc", "cleanup.txt"))

    # 7. Cinnamon thumbnails
    _copy_tree(CINNAMON_SRC, dest)

    # 8. Cinnamon compiled assets (common + light, exclude SCSS sources + dark)
    _copy_tree_filtered(CINNAMON_SCSS, dest / "cinnamon",
                        exclude_files=("*.scss", "meson.build"),
                        exclude_dirs=("dark-assets",))

    # 9. Misc files (exclude shell scripts)
    _copy_tree_filtered(MISC_SRC, dest, exclude_files=("*.sh",))

    # 10. GTK4 CSS
    gtk4_target = dest / "gtk-4.0" / "gtk4.css"
    gtk4_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(gtk4_css, gtk4_target)

    # 10b. Append WinShine CSD overrides for GTK4 (windowcontrols button selectors
    #      pointing to ../gtk-3.0/{csd_dir}/ — compiled CSS still has orb refs)
    csd_dir = csd_css_name.removesuffix(".css")
    with open(gtk4_target, "a") as fh:
        fh.write(_gtk4_csd_block(csd_dir, ws_subdir))

    # 11. Cinnamon compiled CSS
    (dest / "cinnamon").mkdir(parents=True, exist_ok=True)
    shutil.copy2(CINNAMON_CSS, dest / "cinnamon" / "cinnamon.css")


# ── Per-color build ────────────────────────────────────────────────────────────

def build_color(name, bg, fg, version, release):
    print(f"\n── {name.upper()} ({bg}) ──────────────────────────────────")

    print("  Patching source files...")
    patch_colors_scss(bg, fg)
    patch_gtk3_css(bg)
    patch_light_gtkrc(bg)
    for key in ("xfce_blue", "xfce_blue_24", "xfce_blue_28"):
        patch_xfce(key, bg)

    print("  Compiling SCSS...")
    if not compile_scss():
        return False

    print("  Packaging...")
    out_dir = REPO / "build/winshine-light"
    stage   = out_dir / "stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    theme_names = []
    for suffix, gtk_hi, ws_subdir, notify_src, metacity_xml, gtk4_css, base_skip, csd_css_name in _VARIANTS:
        theme_name = f"WinShine-{name}-{version}{suffix}"
        theme_names.append(theme_name)
        dest = stage / theme_name
        dest.mkdir(parents=True, exist_ok=True)
        _build_theme_dir(dest, gtk_hi, ws_subdir, notify_src, metacity_xml,
                         gtk4_css, base_skip, csd_css_name)
        (dest / "index.theme").write_text(_index_theme(theme_name))

    # Remove any previous archives for this color (wildcard, catches old releases)
    for old in out_dir.glob(f"WinShine-{name}-*.tar.gz"):
        old.unlink()

    # Pack all three DPI variants into one archive
    archive = out_dir / f"WinShine-{name}-{version}.{release}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for theme_name in theme_names:
            tar.add(stage / theme_name, arcname=theme_name)

    shutil.rmtree(stage)

    size = archive.stat().st_size // 1024
    print(f"  ✓  {archive.name}  ({size} KB)")
    return True


# ── CLI ────────────────────────────────────────────────────────────────────────

def _read_version():
    props = {}
    for line in (REPO / "GTK-3.22/build.properties").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()
    return props.get("version", "48"), props.get("pkgrelease", "1")


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
        for name, (bg, fg, *_) in COLORS.items():
            print(f"  {name:<10}  bg={bg}  fg={fg}")
        return

    chosen = args.colors or list(COLORS)
    invalid = [c for c in chosen if c not in COLORS]
    if invalid:
        print(f"Unknown color(s): {', '.join(invalid)}")
        print(f"Available: {', '.join(COLORS)}")
        sys.exit(1)

    version, release = _read_version()
    (REPO / "build/winshine-light").mkdir(parents=True, exist_ok=True)

    print(f"Building {len(chosen)} WinShine-light variant(s): {', '.join(chosen)}")
    print(f"Version: {version}.{release}")

    originals = _save()
    failed = []
    try:
        for name in chosen:
            bg, fg, _ = COLORS[name]
            try:
                if not build_color(name, bg, fg, version, release):
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
    print(f"Done. Archives are in {REPO / 'build/winshine-light'}/")


if __name__ == "__main__":
    main()
