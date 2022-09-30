default_scss_files = files([
  '_colors-public.scss',
  '_colors.scss',
  '_common.scss',
  '_drawing.scss',
])

default_theme_variants = [
  'light',
  'dark',
  'lightHi',
  'darkHi',
  'lightUHi',
  'darkUHi'
]

default_theme_deps = []

foreach variant: default_theme_variants
  message('InOut:'+'Default-@0@.scss or css'.format(variant))
  default_theme_deps += custom_target('Default theme variant: ' + variant,
    input: 'Default-@0@.scss'.format(variant),
    output: 'GTK4-@0@.css'.format(variant),
    command: [
      sassc, sassc_opts, '@INPUT@', '@OUTPUT@',
    ],
    depend_files: default_scss_files,
    build_by_default: true
  )
endforeach
