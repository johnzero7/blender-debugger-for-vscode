"""
Build a Blender Extension

1 - Download the denpendencies if needed (Python Wheels). In download_wheels
    Blender docs
    https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html#extensions-python-wheels

2 - Create Blender manifest file (blender_manifest.toml) to define the properties of the extension
    Version, Blender support, license, etc.
    https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html#manifest

3 - Use Blender command line to create the extension package
    https://docs.blender.org/manual/en/latest/advanced/command_line/extension_arguments.html#subcommand-build

"""

import shutil
import subprocess
import tomllib
from pathlib import Path

import tomli_w


def build_for_python(py_tag: str, wheels_src: Path, manifest_overrides: dict) -> None:
    build_dir: Path = Path(f"build_{py_tag}")
    wheels_dest: Path = build_dir / "wheels"
    wheels_dest.mkdir(parents=True, exist_ok=True)

    # Copy code + wheels
    shutil.copytree(
        ".",
        build_dir,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            "build_*",
            "build.py",
            "wheels_*",
            ".git*",
            "__pycache__",
            "downloads_wheels.cmd",
        ),
    )
    for whl in wheels_src.glob("*.whl"):
        shutil.copy(whl, wheels_dest)

    # Update manifest
    manifest_path: Path = build_dir / "blender_manifest.toml"
    with open(manifest_path, "rb") as f:
        data = tomllib.load(f)
    data.update(manifest_overrides)
    data["wheels"] = [f"./wheels/{w.name}" for w in wheels_dest.glob("*.whl")]

    # if the update does not have max version remove it
    if data["blender_version_max"] == "":
        del data["blender_version_max"]

    with open(manifest_path, "wb") as f:
        tomli_w.dump(data, f)

    # Build the extension using blender (use --split-platforms for smaller per-OS zips)
    blender_path = r"D:\SteamLibrary\steamapps\common\Blender\blender.exe"
    subprocess.run(
        [blender_path, "--command", "extension", "build", "--split-platforms"],
        cwd=build_dir,
    )


# Build for Python 3.11 Blender >=4.2 <5.1
build_for_python(
    py_tag="311",
    wheels_src=Path("wheels_311"),
    manifest_overrides={
        "blender_version_min": "4.2.0",  # Introduced extensions. Python 3.11
        "blender_version_max": "5.1.0",  # optional but recommended
        "version": "2.4.0",  # you can bump per target if you want
    },
)

# Build for Python 3.13 Blender >=5.1
build_for_python(
    py_tag="313",
    wheels_src=Path("wheels_313"),
    manifest_overrides={
        "blender_version_min": "5.1.0",
        "version": "2.4.0",
    },
)
