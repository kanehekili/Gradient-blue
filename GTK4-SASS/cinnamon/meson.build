default_scss_files = files([
  '../gtk4/_colors.scss',
  '_common.scss',
  '_drawing.scss',
])

default_theme_variants = [
  'light',
  'dark',
]

# iterate over variatns to get the suffix - maybe later 
#theme_name = meson.project_name() + suffix
theme_name = meson.project_name() #thats Gradient

default_theme_deps = []

foreach variant: default_theme_variants
  message('InOut:'+'Default-@0@.scss or css'.format(variant))
  default_theme_deps += custom_target('Default theme variant: ' + variant,
    input: 'Default-@0@.scss'.format(variant),
    output: 'cinnamon-@0@.css'.format(variant),
    #output: '@0@-@1@.css'.format(theme_name,variant),
    #output: '@0@.css'.format(theme_name),
    command: [
      sassc, sassc_opts, '@INPUT@', '@OUTPUT@',
    ],
    depend_files: default_scss_files,
    build_by_default: true
  )
endforeach