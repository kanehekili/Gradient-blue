Prereqs:
install meson & ninja
Project setup: 
meson setup --buildtype=release --default-library=shared --layout=mirror --optimization=0 --unity=off --warnlevel=1 --wrap-mode=default build

Run:
meson compile -C build