Prereqs:
install sassc, meson & ninja-build
Project setup: (~/git/Gradient-blue/GTK4-SASS)
meson setup --reconfigure --buildtype=release --default-library=shared --layout=mirror --optimization=0 --unity=off --warnlevel=1 --wrap-mode=default build

Run:
meson compile -C build