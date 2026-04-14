#!/usr/bin/env python3
"""
Generic GTK decorator-theme packager driven by a JSON config file.

For each color this script produces one archive under build/{output_subdir}/
containing all DPI variants defined in the config.

Usage:
  python3 generate_theme.py <config.json>                  # build all colors
  python3 generate_theme.py <config.json> green teal       # build specific colors
  python3 generate_theme.py <config.json> --list           # list available colors

Example:
  python3 generate_theme.py configs/winshine.json
"""

import argparse
import json
import shutil
import sys
import tarfile
from pathlib import Path

from build_engine import (
    REPO, GTK4_CSS, CINN_CSS,
    save, restore,
    patch_colors_scss, patch_light, patch_dark,
    compile_scss, read_props,
    copy_tree, copy_tree_filtered,
)
from theme_colors import COLORS

# ── Shared source paths (identical for every decorator config) ────────────────
_GTK_BASE      = REPO / "GTK-3.22/src/Gradient-blue-324.2"
_CINNAMON_SRC  = REPO / "Cinnamon"
_CINNAMON_SCSS = REPO / "GTK4-SASS/cinnamon"
_MISC_SRC      = REPO / "Misc"

# xfce-notify directories — keyed by the gtk_hi path string (None = standard DPI)
_XFCE_NOTIFY = {
    None:
        REPO / "xfwm4/Gradient-blue/xfce-notify-4.0",
    "GTK-3.22/src/Gradient-blue-HiDPI24":
        REPO / "xfwm4/Gradient-blue-HiDPI24/xfce-notify-4.0",
    "GTK-3.22/src/Gradient-blue-HiDPI28":
        REPO / "xfwm4/Gradient-blue-HiDPI28/xfce-notify-4.0",
}


# ── Config loader ─────────────────────────────────────────────────────────────

def load_config(path):
    return json.loads(Path(path).read_text())


# ── GTK4 CSD override block ───────────────────────────────────────────────────

def _gtk4_csd_block(csd_dir, p):
    """Return CSS that overrides GTK4 windowcontrols buttons with decorator images."""
    close_w, small_w, btn_h = p["close_w"], p["small_w"], p["btn_h"]
    img = f"../gtk-3.0/{csd_dir}"
    lines = [
        "\n/* ── Decorator CSD overrides for GTK4 ──────────────────────── */",
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


# ── index.theme ───────────────────────────────────────────────────────────────

def _index_theme(theme_name, comment):
    return (
        "[Desktop Entry]\n"
        "Type=X-GNOME-Metatheme\n"
        f"Name={theme_name}\n"
        f"Comment={comment}\n"
        "Encoding=UTF-8\n"
        "\n"
        "[X-GNOME-Metatheme]\n"
        f"GtkTheme={theme_name}\n"
        f"MetacityTheme={theme_name}\n"
        "IconTheme=elementary-xfce-dark\n"
        "CursorTheme=DMZ-White\n"
        "ButtonLayout=:minimize,maximize,close\n"
    )


# ── Theme directory assembly ───────────────────────────────────────────────────

def _build_theme_dir(dest, v, cfg):
    """Assemble one DPI variant into dest/ according to config and DPI variant v."""
    dec     = REPO / cfg["decorator_src"] / v["decorator_subdir"]
    gtk_hi  = v["gtk_hi"]          # relative path string or null
    csd_css = v.get("csd_css")
    gtk4_p  = v.get("gtk4_csd")

    # 1. GTK base (color-patched css + gtkrc already on disk)
    copy_tree(_GTK_BASE, dest, skip_rel=v["base_skip"])

    # 2. HiDPI GTK overlay
    if gtk_hi:
        copy_tree(REPO / gtk_hi, dest,
                  skip_rel=["index.theme"],
                  skip_dirs=["xfce-notify-4.0"])

    # 3. xfce-notify (color-patched); path derived from gtk_hi
    notify_src = _XFCE_NOTIFY.get(gtk_hi)
    if notify_src is None:
        raise ValueError(f"No xfce-notify mapping for gtk_hi={gtk_hi!r}")
    copy_tree(notify_src, dest / "xfce-notify-4.0")

    # 4. Decorator xfwm4
    copy_tree(dec / "xfwm4", dest / "xfwm4")

    # 5. Decorator gtk-3.0 (CSD files)
    copy_tree(dec / "gtk-3.0", dest / "gtk-3.0")

    # 5b. Generate gtk-decorations.css redirect when csd_css is specified
    if csd_css:
        (dest / "gtk-3.0" / "gtk-decorations.css").write_text(
            f'@import url("{csd_css}");\n'
        )

    # 6. Metacity XML
    meta_dst = dest / "metacity-1"
    copy_tree(REPO / v["metacity_src"], meta_dst)

    # 6b. Copy button PNGs from decorator xfwm4 into metacity-1
    if cfg.get("metacity_pngs_from_decorator", False):
        excludes = tuple(cfg.get("metacity_png_excludes", []))
        copy_tree_filtered(dec / "xfwm4", meta_dst, exclude_files=excludes)

    # 7. Cinnamon thumbnails
    copy_tree(_CINNAMON_SRC, dest)

    # 8. Cinnamon SCSS assets (exclude sources; exclude dark/light assets per variant)
    cinn_excl = "dark-assets" if cfg["variant"] == "light" else "light-assets"
    copy_tree_filtered(_CINNAMON_SCSS, dest / "cinnamon",
                       exclude_files=("*.scss", "meson.build"),
                       exclude_dirs=(cinn_excl,))

    # 9. Misc files
    copy_tree_filtered(_MISC_SRC, dest, exclude_files=("*.sh",))

    # 10. GTK4 CSS
    gtk4_target = dest / "gtk-4.0" / "gtk4.css"
    gtk4_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GTK4_CSS[v["gtk4_key"]], gtk4_target)

    # 10b. Append GTK4 CSD override block when both csd_css and gtk4_csd are present
    if csd_css and gtk4_p:
        with open(gtk4_target, "a") as fh:
            fh.write(_gtk4_csd_block(csd_css.removesuffix(".css"), gtk4_p))

    # 11. Cinnamon compiled CSS
    (dest / "cinnamon").mkdir(parents=True, exist_ok=True)
    shutil.copy2(CINN_CSS[cfg["variant"]], dest / "cinnamon" / "cinnamon.css")


# ── Public API ─────────────────────────────────────────────────────────────────

def package(cfg, name):
    """Package one color for this decorator. Called after SCSS is already compiled."""
    props   = read_props(REPO / "GTK-3.22/build.properties")
    version = props.get("version", "48")
    release = props.get("pkgrelease", "1")
    out_dir = REPO / "build" / cfg["output_subdir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    dec_name = cfg["name"]
    comment  = cfg.get("index_comment", f"A gradient theme with {dec_name} decorations")

    stage = out_dir / "stage"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)

    theme_names = []
    for v in cfg["dpi_variants"]:
        theme_name = f"{dec_name}-{name}-{version}{v['suffix']}"
        theme_names.append(theme_name)
        dest = stage / theme_name
        dest.mkdir(parents=True, exist_ok=True)
        _build_theme_dir(dest, v, cfg)
        (dest / "index.theme").write_text(_index_theme(theme_name, comment))

    for old in out_dir.glob(f"{dec_name}-{name}-*.tar.gz"):
        old.unlink()

    archive = out_dir / f"{dec_name}-{name}-{version}.{release}.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        for theme_name in theme_names:
            tar.add(stage / theme_name, arcname=theme_name)

    shutil.rmtree(stage)
    print(f"  ✓  {archive.name}  ({archive.stat().st_size // 1024} KB)")


def as_profile(cfg):
    """Return a PROFILES entry for build_all.py from a loaded config dict."""
    return {
        "label":   cfg["label"],
        "variant": cfg["variant"],
        "fn":      lambda name, _cfg=cfg: package(_cfg, name),
    }


# ── Standalone build (patch + compile + package) ──────────────────────────────

def build_color(cfg, name, bg, fg_light, fg_dark):
    print(f"\n── {name.upper()} ({bg}) ──────────────────────────────────")
    print("  Patching source files...")
    patch_colors_scss(bg, fg_light, fg_dark)
    if cfg["variant"] == "light":
        patch_light(bg, fg_light)
    else:
        patch_dark(bg, fg_dark)

    print("  Compiling SCSS...")
    if not compile_scss():
        return False

    print("  Packaging...")
    package(cfg, name)
    return True


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("config", help="Path to decorator JSON config file")
    parser.add_argument("colors", nargs="*",
                        help="Colors to build (default: all)")
    parser.add_argument("--list", action="store_true",
                        help="List available colors and exit")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.list:
        for name, (bg, *_) in COLORS.items():
            print(f"  {name:<10}  bg={bg}")
        return

    chosen = args.colors or list(COLORS)
    invalid = [c for c in chosen if c not in COLORS]
    if invalid:
        print(f"Unknown color(s): {', '.join(invalid)}")
        print(f"Available: {', '.join(COLORS)}")
        sys.exit(1)

    print(f"Building {len(chosen)} {cfg['name']} variant(s): {', '.join(chosen)}")

    originals = save()
    failed = []
    try:
        for name in chosen:
            bg, fg_light, fg_dark = COLORS[name]
            try:
                if not build_color(cfg, name, bg, fg_light, fg_dark):
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
    print(f"Done. Archives are in {REPO / 'build' / cfg['output_subdir']}/")


if __name__ == "__main__":
    main()
