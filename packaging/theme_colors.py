"""
Central color palette shared by build_variants.py and build_winshine.py.

Each entry: (bg, fg_light, fg_dark)

  bg        Selection background color.

  fg_light  selected_fg_color for the light GTK3 CSS — the text color shown on
            a selected item in the light theme.  #fff works for dark accent colors;
            use #000000 for bright colors where white text would be unreadable.

  fg_dark   selected_fg_color for the dark GTK3 CSS and GTK4 SCSS — text color
            on a selected item in the dark theme / GTK4.
            A pale tint of bg: same hue, but Lightness pushed to 0.90 in HLS
            space so the text stays readable on the selection background and
            on the selectionHilight gradient top mix(bg, white, 0.3).
            (The old shade(bg, 1.6) recipe produced mid-tones like #A1A4FF
            that were unreadable on selected treeview/calendar/entry text.)
            For a LIGHT bg (e.g. turquoise) the tint flips dark (L = 0.16)
            because pale text has no contrast there.

  To recalculate fg_dark for a new bg:

      import colorsys
      def fg_dark(h):
          r,g,b = (int(h[i:i+2],16)/255 for i in (1,3,5))
          hh,l,s = colorsys.rgb_to_hls(r,g,b)
          lum = 0.2126*r + 0.7152*g + 0.0722*b   # rough luminance
          l = max(min(1,l*1.6), 0.90) if lum < 0.5 else 0.16
          r,g,b = colorsys.hls_to_rgb(hh,l,min(1,s*1.6))
          return f'#{round(r*255):02X}{round(g*255):02X}{round(b*255):02X}'
"""

COLORS = {
    # name:       (bg,        fg_light,   fg_dark)
    "blue":      ("#282DDC", "#fff",     "#CCCDFF"),
    "green":     ("#1A8C2B", "#fff",     "#CCFFD4"),
    "red":       ("#CC2020", "#fff",     "#FFCCCC"),
    "purple":    ("#7B2FBE", "#fff",     "#E7CDFE"),
    "teal":      ("#007878", "#fff",     "#CCFFFF"),
    "orange":    ("#C85700", "#fff", "#FFE2CC"),
    "turquoise": ("#4fe3e3", "#000000",  "#005252"),
}

# shade() factor for the dark GTK3 selectionLolight (the bottom of the
# selection gradient): @define-color selectionLolight shade(@selected_bg_color, FACTOR).
# The default 0.3 suits dark accents.  A LIGHT accent needs a much lighter
# gradient bottom, or its dark fg_dark text vanishes there
# (turquoise: shade(0.3) = #0D4F4F vs fg #005252 -> contrast 1.0:1;
#  shade(0.55) = #189191 -> 2.4:1, close to GTK4's gradient bottom).
DEFAULT_SEL_LOLIGHT = 0.3
SEL_LOLIGHT_FACTOR = {"turquoise": 0.55}

def sel_lolight_factor(name):
    return SEL_LOLIGHT_FACTOR.get(name, DEFAULT_SEL_LOLIGHT)
