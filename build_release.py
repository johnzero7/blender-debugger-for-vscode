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

import os
import re
import shutil
import subprocess
import zipfile
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor, as_completed
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


def blender_build_package(build_path: str, release_path: str) -> None:
    """Run blender commandline to generate the extension packages"""
    cmd = [
        os.environ["BLENDER_PATH"],
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


def download_dependencies_wheels(
    py_tag: str,
    py_platform: str,
    wheels_path: os.PathLike[str] | str,
    build_path: os.PathLike[str] | str,
) -> tuple[str, str, bool, Any]:
    """Download the dependencies wheels for the specified Python version and platform using pip."""
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


def get_current_commit_version(branch: Optional[str]) -> str | None:
    """Get the version from the Git tag of the current commit if it matches the pattern v*.

    Returns:
        The version string without the 'v' prefix, or None if no matching tag is found.
    """
    cmd = ["git", "describe", "--tags", "--exact-match", "--match", "v*"]
    if branch:
        cmd.append(branch)
    try:
        my_tag = (
            subprocess.check_output(
                cmd,
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        )
        return my_tag[1:]
    except subprocess.CalledProcessError:
        return None


def get_most_recent_tag_version(branch: Optional[str]) -> str:
    """Get the version from the Git tag of the most recent commit if it matches the pattern v*.

    Returns:
        The version string without the 'v' prefix, or "0.0.0" if no matching tag is found.
    """
    default = "0.0.0"
    cmd = ["git", "describe", "--tags", "--match", "v*"]
    if branch:
        cmd.append(branch)
    try:
        raw_tag = (
            subprocess.check_output(
                cmd,
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        )
        tag_parts = re.match(r"^v(\d+\.\d+\.\d+)-(\d+)-(\w+)$", raw_tag)
        return default if tag_parts is None else tag_parts.group(1)
    except subprocess.CalledProcessError:
        return default


def get_current_commit_hash(branch: Optional[str] = None) -> str:
    """Get the short hash of the current Git commit.

    Returns:
        The short hash string, or "unknown" if it cannot be retrieved.
    """
    ref = branch or "HEAD"
    cmd = ["git", "rev-parse", "--short", ref]
    try:
        hash = (
            subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
            .decode("utf-8")
            .strip()
        )
        return hash
    except subprocess.CalledProcessError:
        return "unknown"


def is_version_valid(current_version: Optional[str]) -> bool:
    """Check if the provided version string is in the format MAJOR.MINOR.PATCH.

    Args:
        current_version: The version string to validate.

    Returns:
        True if the version is valid, False otherwise.
    """
    is_valid: bool = bool(
        current_version is not None and re.search(r"^\d+\.\d+\.\d+$", current_version)
    )
    return is_valid


def get_fake_version(
    current_version: Optional[str] = None, branch: Optional[str] = None
) -> str:
    """Generate a fake version string for development builds when no Git tag is available.

    Args:
        current_version: The current version from the manifest, if available.
        branch: The Git branch to use for version detection.

    Returns:
        A version string in the format MAJOR.MINOR.(PATCH+1)-dev-SHORT_HASH.
    """

    version = current_version or "0.0.0"
    if not is_version_valid(current_version):
        version = get_most_recent_tag_version(branch)
    hash = get_current_commit_hash(branch)
    major, minor, patch = version.split(".")
    updated_patch = ".".join([major, minor, str(int(patch) + 1)])
    return "-".join([updated_patch, "dev", hash])


def build_package(
    py_tag: str,
    platforms: list[str],
    manifest_overrides: dict[str, Any],
    *,
    branch: Optional[str] = None,
    src_folder: str = "src",
    build_folder: str = "build",
    release_folder: str = "releases",
) -> None:
    """Build the Blender extension package for a specific Python version.

    Downloads required wheels, updates the manifest with version and wheels,
    and builds the extension packages using Blender's command line tool.

    Args:
        py_tag: The Python version tag (e.g., "3.11").
        platforms: List of platform strings for wheel downloads.
        manifest_overrides: Dictionary of overrides for the manifest.
        src_folder: Source folder name (default "src").
        build_folder: Build folder name (default "build").
        release_folder: Release folder name (default "releases").

    Raises:
        RuntimeError: If BLENDER_PATH is not set or invalid, or if no ZIP files are produced.
    """
    if (
        os.environ.get("BLENDER_PATH") is None
        or shutil.which(os.environ["BLENDER_PATH"]) is None
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
            executor.submit(
                download_dependencies_wheels, py_tag, p, wheels_path, build_path
            ): p
            for p in platforms
        }

        for future in as_completed(future_to_platform):
            tag, platform, success, output = future.result()

    # Update the version
    manifest_version: Optional[str] = str(manifest["version"])
    version: Optional[str] = get_current_commit_version(branch)
    fake_version: Optional[str] = None

    if version is None:
        fake_version = get_fake_version(manifest_version, branch)
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

    blender_build_package(str(build_path), str(release_path))

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

    # Build for Python 3.13 Blender >=5.1
    build_package(
        py_tag="3.13",
        platforms=platforms,
        manifest_overrides={
            "blender_version_min": "5.1.0",
        },
    )
