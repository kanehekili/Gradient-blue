project('Gradient',
        version: '4.4.0',
        meson_version: '>= 0.59',
        license : ['GPL3', 'CC BY-SA 4.0'],
        default_options: ['prefix=/usr'])



sassc = find_program('sassc',required:true)

if sassc.found()
	sassc_opts = [ '-a', '-M', '-t', 'compact' ]
endif

components = [
   'gtk4', 
   'gnome-shell'
]
foreach component: components
  message('Enter '+component)
  subdir(component)
endforeach