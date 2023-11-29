#
#    Original code from Robert Guetzkow
#    https://github.com/robertguetzkow/blender-python-examples
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>

"""
This library probvides functionality to manage dependecies of an addon.
Only dependencies that can be installed using PIP are suported.

Some examples are numpy, openCV, debugpy


Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
of the arguments. DO NOT use this to import other parts of your Python add-on, import them as usual with an
"import" statement.



# Define the denpendencies
```
dependencies = (
    Dependency(module="cv2", package="opencv-contrib-python", alias="cv", display_name="OpenCV"),
    Dependency(module="matplotlib", display_name="matplotlib"),
    Dependency(module="numpy", package="numpy", version="==1.26.0"),
    Dependency(module="debugpy", package="debugpy"),
)
```

Pass the globals() to the manager to dinamically import and make the alias available
to other parts of the code
```
dependency_manager.main_globals = globals()
```

Inside the preferences panel draw method call dependency_manager_ui(self, context, layout)

Select to manage the instalations of each package separattly or all together
Default is True
```
dependency_manager.manage_individually = False
```

"""

import importlib
import importlib.metadata
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Any

import bpy

addon_name: str = __package__.replace("-", "_")
# addon_name:None | str = __name__.replace("-", "_")
dependant_classes: tuple[str, ...]


# Dependency = namedtuple("Dependency", ["module", "package", "name"])
@dataclass
class Dependency:
    """
    Class representing a dependency to install with pip

    module : name of the module as written in the import
    package : name of the packae as it appears in pip.
    alias : alias name for the import, global name, (import xxx as yyy)
    display_name : Name only used to display to the user
    version: If a specific version is required put it here using Requirement Specifiers syntax (version="==3.2.1")
    """

    module: str
    package: None | str = None
    alias: None | str = None
    display_name: None | str = None
    version: None | str = None

    def __post_init__(self):
        self.alias = self.alias or self.module
        self.package = self.package or self.module
        self.display_name = self.display_name or self.module


dependencies: tuple[Dependency, ...] | None = None
main_globals: dict[str, Any] | None = None
manage_individually: bool = True


def import_module(
    module_name: str, alias_name: str = None, reload: bool = True
) -> None:
    """
    Import a module.
    :param module_name: Module to import.
    :param alias_name: (Optional) Name under which the module is imported.
        If None, the module_name will be used.
        This allows to import under a different name with the same effect as e.g.
        "import numpy as np" where "np" is the alias_name under which the module can be accessed.
    :raises: ImportError and ModuleNotFoundError
    """
    alias_name = alias_name or module_name
    print(f"IMPORTING {module_name} ...")

    module = None
    if alias_name in sys.modules:
        print(f"{alias_name!r} already in sys.modules")
        return None

    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"can't find the {alias_name!r} module")
        return None

    print(module_name, "--SPEC")
    # If you chose to perform the actual import ...
    module = importlib.util.module_from_spec(spec)

    sys.modules[alias_name] = module
    spec.loader.exec_module(module)
    print(f"{alias_name!r} has been imported")
    return module


def install_pip() -> None:
    """
    Installs pip if not already present. Please note that ensurepip.bootstrap() also calls pip, which adds the
    environment variable PIP_REQ_TRACKER. After ensurepip.bootstrap() finishes execution, the directory doesn't exist
    anymore. However, when subprocess is used to call pip, in order to install a package, the environment variables
    still contain PIP_REQ_TRACKER with the now nonexistent path. This is a problem since pip checks if PIP_REQ_TRACKER
    is set and if it is, attempts to use it as temp directory. This would result in an error because the
    directory can't be found. Therefore, PIP_REQ_TRACKER needs to be removed from environment variables.
    :return:
    """

    try:
        # Check if pip is already installed
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True)
    except subprocess.CalledProcessError:
        import ensurepip

        ensurepip.bootstrap()
        os.environ.pop("PIP_REQ_TRACKER", None)


def install_module(package_name: str, package_requirements: str = None) -> None:
    """
    Installs the package through pip and attempts to import the installed module.
    :param package_name: Name of the package that needs to be installed.
    :raises: subprocess.CalledProcessError
    """

    if package_name is None:
        raise ValueError("Package name not especified")

    # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
    # if a dependency is already installed. This can cause problems if the packages is installed in the user
    # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
    # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
    # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
    # The paths used by pip can be checked with `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

    # Create a copy of the environment variables and modify them for the subprocess call
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    ver = package_requirements or ""
    requirement = f"{package_name}{ver}"
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", requirement],
            check=True,
            env=environ_copy,
        )
    except subprocess.CalledProcessError as e:
        print(e)


def uninstall_module(package_name: str) -> None:
    """
    Uninstalls the package through pip.
    :param package_name: Name of the package that needs to be uninstalled.
    :raises: subprocess.CalledProcessError
    """

    if package_name is None:
        raise ValueError("Package name not especified")

    # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
    # if a dependency is already installed. This can cause problems if the packages is installed in the user
    # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
    # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
    # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
    # The paths used by pip can be checked with `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

    # Create a copy of the environment variables and modify them for the subprocess call
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "--yes", package_name],
            check=True,
            env=environ_copy,
        )
    except subprocess.CalledProcessError as e:
        print(e)


class DEPENDENCY_OT_install_dependencies(bpy.types.Operator):
    bl_idname = f"{addon_name}.install_dependencies"
    bl_label = f"Install {addon_name} dependencies"
    bl_description = (
        "Downloads and installs the required python packages for this add-on. "
        "Internet connection is required. Blender may have to be started with "
        "elevated permissions in order to install the package"
    )
    bl_options = {"REGISTER", "INTERNAL"}

    package_name: bpy.props.StringProperty()

    def execute(self, context):
        if dependencies is None:
            return {"CANCELLED"}

        if self.package_name == "":
            dep_list = dependencies
        else:
            dep_list = (dep for dep in dependencies if dep.package == self.package_name)

        for dep in dep_list:
            try:
                install_module(dep.package, dep.version)
            except (subprocess.CalledProcessError, ImportError) as err:
                self.report({"ERROR"}, str(err))
                return {"CANCELLED"}

        # Register the panels, operators, etc. since dependencies are installed
        register_dependant_classes()

        return {"FINISHED"}


class DEPENDENCY_OT_uninstall_dependencies(bpy.types.Operator):
    bl_idname = f"{addon_name}.uninstall_dependencies"
    bl_label = f"Uninstall {addon_name} dependencies"
    bl_description = (
        "Uninstalls the required python packages for this add-on. "
        "Blender may have to be started with elevated permissions in order to uninstall the package"
    )
    bl_options = {"REGISTER", "INTERNAL"}

    package_name: bpy.props.StringProperty()

    def execute(self, context):
        if dependencies is None:
            return {"CANCELLED"}

        if self.package_name == "":
            dep_list = dependencies
        else:
            dep_list = (dep for dep in dependencies if dep.package == self.package_name)

        for dep in dep_list:
            try:
                uninstall_module(dep.package)
            except (subprocess.CalledProcessError, ImportError) as err:
                self.report({"ERROR"}, str(err))
                return {"CANCELLED"}

        unregister_dependant_classes()

        return {"FINISHED"}


def import_all_dependencies() -> None:
    """Try to import all dependencies"""
    if dependencies is None:
        return

    for module in dependencies:
        try:
            import_module(module_name=module.module, alias_name=module.alias)
        except ImportError:
            print(f"Could not import module {module}")


def check_all_dependencies() -> bool:
    """True if all dependencies are installed"""
    if dependencies is None:
        return False

    return all(check_dependency_state(dep) for dep in dependencies)


def update_dependencies_states() -> None:
    """True if all dependencies are installed"""
    if dependencies is None:
        return

    for dep in dependencies:
        check_dependency_state(dep)


def check_dependency_state(dep: Dependency) -> bool:
    """True if the dependency is installed"""
    if dep is None:
        return False

    if dep.module in sys.modules:
        return True
    elif importlib.util.find_spec(dep.module) is not None:
        return True
    else:
        return False

    return False


def check_module_version(module: str, package: str = None) -> bool:
    """
    Return the version of the installed module.
    If not installed returns None
    https://docs.python.org/3/library/importlib.html#checking-if-a-module-can-be-imported
    """
    ver = None
    package = package or module
    try:
        spec = importlib.util.find_spec(module)
    except ValueError:
        spec = None
    if spec is not None:
        try:
            ver = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            ver = None
    return ver


def dependency_manager_ui(self, context, layout=None) -> None:
    # Element is a UI element, such as layout, a row, column, or box.
    layout = layout or self.layout
    box = layout.box()

    if dependencies is None:
        box.label(text="No dependencies have been defined")
        return

    if main_globals is None:
        box.label(text="Main globals is not asigned")
        return

    for dep in dependencies:
        ver = check_module_version(dep.module, dep.package)
        installed = ver is not None
        row1 = box.row()
        # Check if dependencies are installed

        if installed:
            installation_status_msg = (
                f"Dependency Status: {dep.display_name} {ver} is installed."
            )
        else:
            installation_status_msg = (
                f"Dependency Status: {dep.display_name} not found."
            )
        row1.label(text=installation_status_msg)

        if manage_individually:
            row2 = box.row()
            if installed:
                uninstall_button = row2.operator(
                    DEPENDENCY_OT_uninstall_dependencies.bl_idname,
                    text="Unistall depencies",
                    icon="CONSOLE",
                )
                uninstall_button.package_name = dep.package
            else:
                install_button = row2.operator(
                    DEPENDENCY_OT_install_dependencies.bl_idname,
                    text="Install depencies",
                    icon="CONSOLE",
                )
                install_button.package_name = dep.package

    if not manage_individually:
        row3 = box.row()
        if check_all_dependencies():
            row3.label(text="All dependencies are installed")
        else:
            row3.label(text="Some dependencies are missing")
        row4 = box.row()
        install_all_button = row4.operator(
            DEPENDENCY_OT_install_dependencies.bl_idname,
            text="Install all depencies",
            icon="CONSOLE",
        )
        install_all_button.package_name = ""
        uninstall_all_button = row4.operator(
            DEPENDENCY_OT_uninstall_dependencies.bl_idname,
            text="Unistall all depencies",
            icon="CONSOLE",
        )
        uninstall_all_button.package_name = ""


def register_dependant_classes():
    """Register dependant classes but checking if they are registered"""
    # Register dependant classes
    if not check_all_dependencies():
        return
    for cls in dependant_classes:
        if not cls.is_registered:
            bpy.utils.register_class(cls)


def unregister_dependant_classes():
    """Unregister dependant classes but checking if they are registered"""
    # Unregister dependant classes
    for cls in dependant_classes:
        if cls.is_registered:
            bpy.utils.unregister_class(cls)


manager_classes = (
    DEPENDENCY_OT_install_dependencies,
    DEPENDENCY_OT_uninstall_dependencies,
)


# Use factory to create method to register and unregister the dependency manager classes
register_classes, unregister_classes = bpy.utils.register_classes_factory(
    manager_classes
)


def register():
    install_pip()
    register_classes()
    update_dependencies_states()
    register_dependant_classes()


def unregister():
    unregister_classes()
    unregister_dependant_classes()
