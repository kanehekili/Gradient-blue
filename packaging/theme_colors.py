"""
Central color palette shared by build_variants.py and build_winshine.py.

Each entry: (bg, fg_light, fg_dark)

  bg        Selection background color.

  fg_light  selected_fg_color for the light GTK3 CSS — the text color shown on
            a selected item in the light theme.  #fff works for dark accent colors;
            use #000000 for bright colors where white text would be unreadable.

  fg_dark   selected_fg_color for the dark GTK3 CSS and GTK4 SCSS — text color
            on a selected item in the dark theme / GTK4.
            Computed as GTK's shade(bg, 1.6), which scales both Lightness and
            Saturation by 1.6 in HLS space (clamped to 1.0).
            The dark GTK3 template already expresses this as a runtime formula
            shade(@selected_bg_color, 1.6); the value here is used to patch
            the compiled GTK4 CSS so it matches exactly.

  To recalculate fg_dark for a new bg:

      import colorsys
      def shade16(h):
          r,g,b = (int(h[i:i+2],16)/255 for i in (1,3,5))
          hh,l,s = colorsys.rgb_to_hls(r,g,b)
          l,s = min(1,l*1.6), min(1,s*1.6)
          r,g,b = colorsys.hls_to_rgb(hh,l,s)
          return f'#{round(r*255):02X}{round(g*255):02X}{round(b*255):02X}'
"""

COLORS = {
    # name:       (bg,        fg_light,   fg_dark)
    "blue":      ("#282DDC", "#fff",     "#A1A4FF"),
    "green":     ("#1A8C2B", "#fff",     "#0BFF2F"),
    "red":       ("#CC2020", "#fff",     "#FF7B7B"),
    "purple":    ("#7B2FBE", "#fff",     "#C27EFD"),
    "teal":      ("#007878", "#fff",     "#00C0C0"),
    #"orange":    ("#FF991C", "#000000",  "#FFE5C6"),
    "orange":    ("#C85700", "#fff", "#FFD0AD"),
    "turquoise": ("#4fe3e3", "#000000",  "#EBFFFF"),
}
