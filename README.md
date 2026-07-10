# Gradient-blue & Gradient-black
Gradient-blue (light) 48.5 · Gradient-black (dark) 48.6

A GTK theme supporting gtk2,gtk3 and gtk4 

This theme was written for the GTK3.20+ and the GTK 3.18 Version and includes a matching gtk2 Version. It is supposed to be the anti thesis of the flat "material design" and has gradients!

The GTK4 Version is finalized and supports up to GTK4.8

Gradient-blue has been extended with Gradient-black, which is based on the gray theme but was completely rewritten...

The theme has been tested with LXDE(GTK), xfce, openbox, cinnamon and gnome (40-48)

## How to install
Download the tar.gz file and extract it into one of:
* `~/.themes` — classic per-user location (GTK2, GTK3, GTK4 and most DE tools read it)
* `~/.local/share/themes` — XDG per-user location (preferred if you use Flatpak apps)
* `/usr/share/themes` — system-wide, all users

Then select the theme with your desktop's appearance tool
(Xfce: Settings → Appearance, Cinnamon: System Settings → Themes,
GNOME: gnome-tweaks → Appearance → "Legacy Applications", LXDE: lxappearance).

Can be downloaded via pling:
* [GradientBlue](https://www.gnome-look.org/p/1185760/)
* [GradientBlack](https://www.gnome-look.org/p/1424967/)

## Making sure the theme is applied

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
* GNOME/Cinnamon/Budgie: `gsettings set org.gnome.desktop.interface gtk-theme 'Gradient-blue'`
  (Cinnamon additionally: `org.cinnamon.desktop.interface gtk-theme`)
* Xfce: `xfconf-query -c xsettings -p /Net/ThemeName -s Gradient-blue`
* No DE daemon (openbox, i3, …): `~/.config/gtk-3.0/settings.ini`

      [Settings]
      gtk-theme-name=Gradient-blue

### GTK4 applications
Plain GTK4 applications follow the same theme name and automatically load the
`gtk-4.0/gtk.css` shipped inside the theme — nothing extra to do.

**libadwaita** applications (most modern GNOME apps) ignore the selected theme.
Two ways to theme them anyway:

1. Force the theme globally in `/etc/environment` (re-login afterwards):

       GTK_THEME=Gradient-blue

   This affects all GTK3/GTK4 apps. Note that `GTK_THEME` is technically a
   debugging variable: it overrides the light/dark preference, so pick the
   variant you want by name (e.g. `GTK_THEME=Gradient-black` for dark).

2. Per-user, without an environment variable — link the theme's GTK4 CSS into
   your config (both files are needed, `gtk.css` imports `gtk4.css`):

       mkdir -p ~/.config/gtk-4.0
       ln -sf ~/.themes/Gradient-blue/gtk-4.0/gtk.css  ~/.config/gtk-4.0/gtk.css
       ln -sf ~/.themes/Gradient-blue/gtk-4.0/gtk4.css ~/.config/gtk-4.0/gtk4.css

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

## Hi DPI Versions
The HIDPI Versions provide different resolutions for metacity,xfwm4 and GTK-CSD. 
They are contained in the download.

## Supported desktops
* gnome
* xfce
* cinnamon
* lxde

## License
All themes are dual-licensed as GPLv2 or later and CC-BY-SA 3.0 or later.

## Versions
| Version | Date |Changelog|
| ------------- | ------------- |------------- |
| 48.6   | 11.07.26  |Dark theme: readable selection text per accent color, softer turquoise selection gradient, GTK4 treeview hover tint, new WinShine-dark packages|
| 48.5   | 25.05.26  |xfwm4 button size fix|
| 48.3   | 14.04.26  |WinShine decorator packages, color & selection fixes|
| 4.7.3  | 12.12.25  |Ptyxis Tabs, notebook tabs|
| 4.7.2  | 12.12.25  |GTK4 fixes|
| 4.6.2  | 01.11.22  |GTK3/4 Menues/popover refinement| 
| 4.6.1  | 15.10.22  |Updated to GTK 4.8, Cinnamon themes|
| 4.6    | 01.10.22  |Created GTK4.6 theme from scratch, Improved gtk3+gnome.shell|
| 420.2  | 04.06.22  |Fixed colors and GTK4 specific widgets|
| 420.0  | 29.05.22  |Gradient-black GTK-4.0 support|
| 325.6  | 23.10.21  |Gradient-blue CSD-shadows,revealer theme 6 round switches|
| 326.6  | 23.10.21  |Gradient-black CSD-shadows,revealer theme & round switches|
| 325    | 04.12.20  |Gradient-blue lightdm & gnome-shell fixes,XFWM4 & metacity redesign|
| 326    | 04.12.20  |Gradient-black lightdm & gnome-shell fixes,XFWM4 & metacity redesign|
| 325.1  | 29.10.20  |Gradient-black with lightdm and gnome shell|
| 325.0  | 20.09.20  |introduction Gradient-black|
| 324.2  | 24.04.20  |xfwm4,metacity and GTK3-CSD new orbs + HI DPI|
| 324.1  | 27.02.20  |Backdrops checkbuttons|
| 324.0  | 19.12.19  |Minor fixes for gtk3 (backdrops) and metacity|
| 323.1  | 22.03.19  |Fixed Backdrop issues & Notebook refactoring|
| 323.0  | 22.12.18  |Fixed some entry geometry (Eclipse) |
| 322.3  | 10.08.17  |Added Gnome-shell on base of the numix theme. Fixed a cinnomon issue. Minor changes one notebooks |
| 322.2  | 28.07.17  |Initial commit|

## Screenshots GTK3.22+

More pictures on Opendesk for [Black](https://www.pling.com/p/1424967/) and [Blue](https://www.gnome-look.org/p/1185760/)

Gradient-black
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.22-dark/widget-factory.png)

Gradient-blue
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.22/Gradient-blue-3.22-WF.png)

Gnome 3.24 - Gradient-blue
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.22/Gnome322.png)

## HiDPI Screenshot on Ubuntu 20.04 - Gradient-blue
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.22/Ubuntu20.04.png)

## Screenshots GTK3.18 (legacy) - Gradient-blue
The widget factory
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.18/Gradient-blue-WF.png)

Nemo file manager
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.18/Gradient-blue-nemo.png)

PCmanFM filemanager 
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.18/Gradient-blue-pcmanfm.png)

Pix photo editor
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.18/Gradient-blue-pix.png)

## Screenshot GTK4.x
Ptyxis Terminal
![Screenshot](https://github.com/kanehekili/Gradient-blue/blob/master/GTK-3.22-dark/ptyxis.png)
