"""
This script adds a few niceties on top of the Blender extension builder:

- Download the wheels from the src/requirements.txt file
    https://docs.blender.org/manual/en/latest/advanced/extensions/python_wheels.html#extensions-python-wheels
- Update the blender_manifest.toml with the wheels, version from Git tag if it is set to vMAJOR.MINOR.PATCH
    https://docs.blender.org/manual/en/latest/advanced/extensions/getting_started.html#manifest
- Generates a "fake" version tag if there is no Git tag set
- Use Blender command line to create the extension packages for the platforms
    https://docs.blender.org/manual/en/latest/advanced/command_line/extension_arguments.html#subcommand-build
- Includes any files/directories/globs specified in the blender_manifest.toml "parent_files" array


It requires the "tomlkit" and "python-dotenv" packages to be installed (included in the requirements.txt file),
and requires the BLENDER_PATH environment variable to be set to the path of
the Blender executable used for building. This can be set in a
.env file in the root of the repository, or by setting the environment
variable before running the script..

To use:

BLENDER_PATH=/path/to/blender python3 build_release.py

(or if you set up the .env file already)

python build_release.py
"""

import re
import shutil
import subprocess
import zipfile
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
from os import PathLike, environ
from pathlib import Path
from typing import Any, Optional

import tomlkit
from dotenv import load_dotenv

load_dotenv()

blender_platforms: list[str] = [
    "windows-x64",
    "windows-arm64",
    "macos-x64",
    "macos-arm64",
    "linux-x64",
]


def run_platform(
    py_tag: str,
    py_platform: str,
    wheels_path: PathLike[str] | str,
    build_path: PathLike[str] | str,
) -> tuple[str, str, bool, Any]:
    """Function that runs one subprocess"""
    cmd = [
        "py",
        "-m",
        "pip",
        "download",
        "--no-deps",
        "--only-binary=:all:",
        "--python-version",
        py_tag,
        "--platform",
        py_platform,
        "-r",
        "requirements.txt",
        "--dest",
        wheels_path,
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=build_path,
        )

        return py_tag, py_platform, True, result.stdout

    except subprocess.CalledProcessError as e:
        print(f"{py_tag} {py_platform} - Failed: {e.stderr.strip()}")
        return py_tag, py_platform, False, e.stderr
    except Exception as e:
        print(f"{py_tag} {py_platform} - Error: {e}")
        return py_tag, py_platform, False, str(e)


def get_version() -> str | None:
    try:
        my_tag = (
            subprocess.check_output(
                ["git", "describe", "--tags", "--exact-match", "--match", "v*"],
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        )
        return my_tag[1:]
    except subprocess.CalledProcessError:
        return None


def get_fake_version(current_version: Optional[str] = None) -> str:
    invalid_ver: bool = current_version is None or not re.search(
        r"^\d+\.\d+\.\d+$", current_version
    )
    if invalid_ver:
        try:
            raw_tag = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--match", "v*"],
                    stderr=subprocess.DEVNULL,
                )
                .decode("utf-8")
                .strip()
            )
            tag_parts = re.match(r"^v(\d+\.\d+\.\d+)-(\d+)-([a-z0-9]+)$", raw_tag)
            current_version = "0.0.0" if tag_parts is None else tag_parts.group(1)
        except subprocess.CalledProcessError:
            current_version = "0.0.0"
            pass
    cmd = ["git", "rev-parse", "--short", "HEAD"]
    hash = (
        subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode("utf-8").strip()
    )
    parts = current_version.split(".")
    return ".".join(parts[0:2] + [str(int(parts[2]) + 1)]) + "-dev-" + hash


def build_package(
    py_tag: str,
    platforms: list,
    manifest_overrides: dict,
    src_folder: str = "src",
    build_folder: str = "build",
    release_folder: str = "releases",
) -> None:
    if (
        environ.get("BLENDER_PATH") is None
        or shutil.which(environ["BLENDER_PATH"]) is None
    ):
        raise RuntimeError(
            "BLENDER_PATH environment variable must be set to the path of the Blender executable."
        )

    py_ver: str = py_tag.replace(".", "")

    src_path: Path = Path(src_folder)
    build_path: Path
    if not py_tag:
        build_path = Path(build_folder)
        release_path = Path(release_folder)
    else:
        build_path = Path(f"{build_folder}_{py_ver}")
        release_path = Path(f"{release_folder}_{py_ver}")

    release_path.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        src_path,
        build_path,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(
            ".git*",
            "__pycache__",
        ),
    )

    # read source manifest
    with open(src_path / "blender_manifest.toml", "r") as in_file:
        manifest: tomlkit.TOMLDocument = tomlkit.load(in_file)

    parent_files: list[str] = manifest.get("build", {}).get("parent_files", [])
    wheels_dir: str = manifest.get("build", {}).get("wheels_dir", "wheels")
    wheels_path: Path = Path(wheels_dir)

    # download all the required wheels
    with ProcessPoolExecutor(max_workers=4) as executor:
        future_to_platform = {
            executor.submit(run_platform, py_tag, p, wheels_path, build_path): p
            for p in platforms
        }

        for future in as_completed(future_to_platform):
            tag, platform, success, output = future.result()

    # Update the version
    manifest_version: Optional[str] = str(manifest["version"])
    version: Optional[str] = get_version()
    fake_version: Optional[str] = None

    if version is None:
        fake_version = get_fake_version(manifest_version)
        print(
            f"There is no version tag on this commit, so using a temporary build version of {fake_version}"
        )

    manifest["version"] = version or fake_version

    build_wheels_path = build_path / wheels_path
    wheels: Iterator[Path] = build_wheels_path.glob("*.whl")
    wheels_toml = ["./" + p.relative_to(build_path).as_posix() for p in wheels]
    array = tomlkit.array()
    array.extend(wheels_toml)
    manifest["wheels"] = array.multiline(True)
    manifest.update(manifest_overrides)

    # if the update does not have max version remove it
    if (
        manifest["blender_version_max"] == ""
        or "blender_version_max" not in manifest_overrides
    ):
        del manifest["blender_version_max"]

    with open(build_path / "blender_manifest.toml", "w") as out_file:
        tomlkit.dump(manifest, out_file)

    # Run blender commandline to generate the packages
    cmd = [
        environ["BLENDER_PATH"],
        "--factory-startup",
        "--command",
        "extension",
        "build",
        "--verbose",
        "--split-platforms",
        "--source-dir",
        build_path,
        "--output-dir",
        release_path,
    ]
    subprocess.run(cmd)

    zips = list(release_path.glob("*.zip"))
    if not zips:
        raise RuntimeError("The build process did not produce a file.")

    # add aditional files to the resulting ZIPs
    for zip_file in zips:
        with zipfile.ZipFile(zip_file, "a") as zip_ref:
            for globulet in parent_files:
                for file in Path(".").glob(globulet):
                    print(f"+ Adding {file.relative_to('.')} to archive...")
                    zip_ref.write(
                        file,
                        arcname=file.relative_to("."),
                        compress_type=zipfile.ZIP_DEFLATED,
                        compresslevel=9,
                    )


if __name__ == "__main__":

    platforms = [
        "win_amd64",
        "macosx_15_0_universal2",
        "manylinux_2_34_x86_64",
    ]

    # Build for Python 3.11 Blender >=4.2
    build_package(
        py_tag="3.11",
        platforms=platforms,
        manifest_overrides={
            "blender_version_min": "4.2.0",  # Introduced extensions. Python 3.11
            "blender_version_max": "5.1.0",  # optional but recommended
            "version": "3.0.0",  # you can bump per target if you want
        },
    )

    # Build for Python 3.13 Blender >=5.1
    build_package(
        py_tag="3.13",
        platforms=platforms,
        manifest_overrides={
            "blender_version_min": "5.1.0",
            "version": "3.0.0",
        },
    )
