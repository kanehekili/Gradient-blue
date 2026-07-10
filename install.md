  ## Making sure the theme is applied

  ### Where to install
  Extract the tar.gz into one of:
  * `~/.themes` — classic per-user location (GTK2, GTK3, GTK4 and most DE tools
  read it)
  * `~/.local/share/themes` — XDG per-user location (preferred if you use
  Flatpak apps)
  * `/usr/share/themes` — system-wide, all users

  Then select the theme with your desktop's appearance tool
  (Xfce: Settings → Appearance, Cinnamon: System Settings → Themes,
  GNOME: gnome-tweaks → Appearance → "Legacy Applications", LXDE: lxappearance).

  ### GTK2 applications
  The GTK2 part needs the murrine and pixmap theme engines. Install:
  * Debian / Ubuntu / Mint: `gtk2-engines-murrine gtk2-engines-pixbuf`
  * Arch / Manjaro: `gtk-engine-murrine gtk-engines`
  * Fedora: `gtk-murrine-engine gtk2-engines`
  * openSUSE: `gtk2-engine-murrine gtk2-engines`

  The theme name for GTK2 is set in `~/.gtkrc-2.0` — appearance tools such as
  lxappearance or the Xfce settings write this file for you:

      gtk-theme-name="Gradient-blue"

  ### GTK3 applications
  Any of these works (the DE tools do it for you):
  * GNOME/Cinnamon/Budgie: `gsettings set org.gnome.desktop.interface gtk-theme
  'Gradient-blue'`
    (Cinnamon additionally: `org.cinnamon.desktop.interface gtk-theme`)
  * Xfce: `xfconf-query -c xsettings -p /Net/ThemeName -s Gradient-blue`
  * No DE daemon (openbox, i3, …): `~/.config/gtk-3.0/settings.ini`

        [Settings]
        gtk-theme-name=Gradient-blue

  ### GTK4 applications
  Plain GTK4 applications follow the same theme name and automatically load the
  `gtk-4.0/gtk.css` shipped inside the theme — nothing extra to do.

  **libadwaita** applications (most modern GNOME apps) ignore the selected
  theme.
  Two ways to theme them anyway:

  1. Force the theme globally in `/etc/environment` (re-login afterwards):

         GTK_THEME=Gradient-blue

     This affects all GTK3/GTK4 apps. Note that `GTK_THEME` is technically a
     debugging variable: it overrides the light/dark preference, so pick the
     variant you want by name (e.g. `GTK_THEME=Gradient-black` for dark).

  2. Per-user, without an environment variable — link the theme's GTK4 CSS into
     your config (both files are needed, `gtk.css` imports `gtk4.css`):

         mkdir -p ~/.config/gtk-4.0
         ln -sf ~/.themes/Gradient-blue/gtk-4.0/gtk.css
  ~/.config/gtk-4.0/gtk.css
         ln -sf ~/.themes/Gradient-blue/gtk-4.0/gtk4.css
  ~/.config/gtk-4.0/gtk4.css

  If you use a dark variant, also tell libadwaita apps to prefer dark colors:

      gsettings set org.gnome.desktop.interface color-scheme prefer-dark

  ### Flatpak applications
  Flatpak apps run sandboxed and cannot see `~/.themes`. Install the theme into
  `~/.local/share/themes` and grant access:

      flatpak override --user --filesystem=xdg-data/themes
      flatpak override --user --env=GTK_THEME=Gradient-blue

  ### Window borders
  On Xfce the window border (xfwm4) is selected separately under
  Settings → Window Manager → Style; pick the matching entry. On Cinnamon/GNOME
  (metacity/gnome-shell) the theme tool picks it up from the same theme folder.

