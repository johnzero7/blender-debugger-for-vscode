@REM -- Create the wheel for debugpy in the ./wheels folder
@REM -- Update for the Python version bundled in Blender intended version

@REM For python 3.11
py -m pip download debugpy --python-version 3.11 --dest ./wheels_311 --no-deps --only-binary=:all: --platform=macosx_15_0_universal2
py -m pip download debugpy --python-version 3.11 --dest ./wheels_311 --no-deps --only-binary=:all: --platform=manylinux_2_34_x86_64
py -m pip download debugpy --python-version 3.11 --dest ./wheels_311 --no-deps --only-binary=:all: --platform=win_amd64
@REM py -m pip download debugpy --python-version 3.11 --dest ./wheels_311 --no-deps --only-binary=:all: --platform=none

@REM For python 3.13
py -m pip download debugpy --python-version 3.13 --dest ./wheels_313 --no-deps --only-binary=:all: --platform=macosx_15_0_universal2
py -m pip download debugpy --python-version 3.13 --dest ./wheels_313 --no-deps --only-binary=:all: --platform=manylinux_2_34_x86_64
py -m pip download debugpy --python-version 3.13 --dest ./wheels_313 --no-deps --only-binary=:all: --platform=win_amd64
@REM py -m pip download debugpy --python-version 3.13 --dest ./wheels_313 --no-deps --only-binary=:all: --platform=none


