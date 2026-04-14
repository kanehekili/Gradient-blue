"""
Shared build engine for Gradient-blue theme variants.

Provides patching, SCSS compilation, and file assembly utilities used by
build_variants.py, build_winshine.py, and build_all.py.
"""

import fnmatch
import os
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent.resolve()

# ── Compiled GTK4 CSS paths (written by compile_scss) ────────────────────────
GTK4_CSS = {
    "light":    REPO / "GTK4-SASS/build/gtk4/GTK4-light.css",
    "dark":     REPO / "GTK4-SASS/build/gtk4/GTK4-dark.css",
    "lightHi":  REPO / "GTK4-SASS/build/gtk4/GTK4-lightHi.css",
    "darkHi":   REPO / "GTK4-SASS/build/gtk4/GTK4-darkHi.css",
    "lightUHi": REPO / "GTK4-SASS/build/gtk4/GTK4-lightUHi.css",
    "darkUHi":  REPO / "GTK4-SASS/build/gtk4/GTK4-darkUHi.css",
}

# ── Cinnamon / misc shared source paths ──────────────────────────────────────
CINNAMON_SRC  = REPO / "GTK4-SASS/cinnamon-thumbnails"
CINNAMON_SCSS = REPO / "GTK4-SASS/cinnamon"
CINN_CSS = {
    "light": REPO / "GTK4-SASS/build/cinnamon/cinnamon-light.css",
    "dark":  REPO / "GTK4-SASS/build/cinnamon/cinnamon-dark.css",
}
MISC_SRC = REPO / "misc"


# ── Source files patched per color (always saved and restored) ────────────────
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

def save():
    return {k: v.read_text() for k, v in _patched_files().items()}

def restore(originals):
    for k, text in originals.items():
        _patched_files()[k].write_text(text)


# ── Patch helpers ─────────────────────────────────────────────────────────────
def _sub(path, pattern, replacement):
    text = path.read_text()
    new, n = re.subn(pattern, replacement, text)
    if n == 0:
        print(f"  WARNING: pattern not found in {path.name}")
    path.write_text(new)

def patch_colors_scss(bg, fg_light, fg_dark):
    f = _patched_files()["colors_scss"]
    text = f.read_text()
    text = re.sub(r'(\$selected_bg_color\s*:).*?;', rf'\g<1>{bg};', text)
    text = re.sub(
        r"(\$selected_fg_color\s*:.*?'light',\s*)#[0-9A-Fa-f]{3,6}(,\s*)#[0-9A-Fa-f]{3,6}",
        rf'\g<1>{fg_light}\g<2>{fg_dark}',
        text
    )
    f.write_text(text)

def patch_gtk3_css(key, bg):
    _sub(_patched_files()[key],
         r'(@define-color selected_bg_color\s+)#[0-9A-Fa-f]{6}(;)',
         rf'\g<1>{bg}\g<2>')

def patch_light_sel_fg(fg_light):
    _sub(_patched_files()["light_css"],
         r'(@define-color selected_fg_color\s+)#[0-9A-Fa-f]{3,6}(;)',
         rf'\g<1>{fg_light}\g<2>')

def patch_light_gtkrc(bg):
    _sub(_patched_files()["light_gtkrc"],
         r'(selected_bg_color:)#[0-9A-Fa-f]{6}',
         rf'\g<1>{bg}')

def patch_light_gtkrc_fg(fg_light):
    _sub(_patched_files()["light_gtkrc"],
         r'(selected_fg_color:)#[0-9A-Fa-f]{3,6}',
         rf'\g<1>{fg_light}')

def patch_dark_gtkrc(bg):
    _sub(_patched_files()["dark_gtkrc"],
         r'(gtk_color_scheme\s*=\s*"selected_bg_color:)(#[0-9A-Fa-f]{6})(")',
         rf'\g<1>{bg}\g<3>')

def patch_xfce(key, bg):
    _sub(_patched_files()[key],
         r'(@define-color selected_xfce_bg_color\s+)#[0-9A-Fa-f]{6}(;)',
         rf'\g<1>{bg}\g<2>')

def patch_dark_sel_fg(fg_dark):
    _sub(_patched_files()["dark_css"],
         r'(@define-color selected_fg_color\s+)#[0-9A-Fa-f]{3,6}(;)',
         rf'\g<1>{fg_dark}\g<2>')

def patch_dark_gtkrc_fg(fg_dark):
    _sub(_patched_files()["dark_gtkrc"],
         r'(selected_fg_color:)#[0-9A-Fa-f]{3,6}',
         rf'\g<1>{fg_dark}')

def patch_light(bg, fg_light):
    """Patch all light-theme source files."""
    patch_gtk3_css("light_css", bg)
    patch_light_sel_fg(fg_light)
    patch_light_gtkrc(bg)
    patch_light_gtkrc_fg(fg_light)
    for key in ("xfce_blue", "xfce_blue_24", "xfce_blue_28"):
        patch_xfce(key, bg)

def patch_dark(bg, fg_dark):
    """Patch all dark-theme source files."""
    patch_gtk3_css("dark_css", bg)
    patch_dark_sel_fg(fg_dark)
    patch_dark_gtkrc(bg)
    patch_dark_gtkrc_fg(fg_dark)
    for key in ("xfce_black", "xfce_black_24", "xfce_black_28"):
        patch_xfce(key, bg)


# ── SCSS compilation ──────────────────────────────────────────────────────────
def compile_scss():
    gtk4_src = REPO / "GTK4-SASS/gtk4"
    cinn_src = REPO / "GTK4-SASS/cinnamon"
    gtk4_out = REPO / "GTK4-SASS/build/gtk4"
    cinn_out = REPO / "GTK4-SASS/build/cinnamon"
    gtk4_out.mkdir(parents=True, exist_ok=True)
    cinn_out.mkdir(parents=True, exist_ok=True)

    jobs = [
        (gtk4_src / "Default-light.scss",    GTK4_CSS["light"]),
        (gtk4_src / "Default-dark.scss",     GTK4_CSS["dark"]),
        (gtk4_src / "Default-lightHi.scss",  GTK4_CSS["lightHi"]),
        (gtk4_src / "Default-darkHi.scss",   GTK4_CSS["darkHi"]),
        (gtk4_src / "Default-lightUHi.scss", GTK4_CSS["lightUHi"]),
        (gtk4_src / "Default-darkUHi.scss",  GTK4_CSS["darkUHi"]),
        (cinn_src / "Default-light.scss",    CINN_CSS["light"]),
        (cinn_src / "Default-dark.scss",     CINN_CSS["dark"]),
    ]
    for src, out in jobs:
        r = subprocess.run(["sassc", "-t", "compact", str(src), str(out)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"  ERROR sassc {src.name}:\n{r.stderr[:300]}")
            return False
    return True


# ── Build properties ──────────────────────────────────────────────────────────
def read_props(path):
    props = {}
    for line in Path(path).read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            props[k.strip()] = v.strip()
    return props


# ── File utilities ────────────────────────────────────────────────────────────
def copy_tree(src, dst, skip_rel=(), skip_dirs=()):
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

def copy_tree_filtered(src, dst, exclude_files=(), exclude_dirs=()):
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

def copy_orbs(metacity_src, dest_csd):
    """Copy *-orb* files from metacity_src/metacity-1/ into dest_csd/."""
    src = Path(metacity_src) / "metacity-1"
    dst = Path(dest_csd)
    dst.mkdir(parents=True, exist_ok=True)
    for f in src.glob("*-orb*"):
        shutil.copy2(f, dst / f.name)

def write_index(index_src, dest_dir, token_value):
    """Copy index.theme replacing @xxxx@ with token_value."""
    text = Path(index_src).read_text().replace("@xxxx@", token_value)
    (Path(dest_dir) / "index.theme").write_text(text)
