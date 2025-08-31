project(
    'icsim',
    'c',
    license: 'GPL-3',
    default_options: [
        'warning_level=2',
    ]
)

find_program('candump', required: true)
deps = [
    dependency('sdl2', required: true),
    dependency('SDL2_image', required: true)
]

subdir('art')
subdir('data')

executable('icsim', ['icsim.c', 'lib.c'], dependencies: deps)
executable('controls', 'controls.c', dependencies: deps)
