#
#    Original code from Robert Guetzkow
#    https://github.com/robertguetzkow/blender-python-examples/tree/master/add_ons/install_dependencies
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

import importlib
import importlib.metadata
import os
import subprocess
import sys

# from collections import namedtuple
from dataclasses import dataclass

import bpy.utils

addon_name = __package__.replace("-", "_")


# Dependency = namedtuple("Dependency", ["module", "package", "name"])
@dataclass
class Dependency:
    """
    Class representing a dependency to install with pip

    module : name of the module as written in the import
    package : name of the packae as it appears in pip
    name : alias name for the import
    display_name : Commercial name of the package
    installed : flag if the pacakage is installed
    """

    display_name: str
    module: str
    package: str = None
    name: str = None
    installed: bool = False


def import_module(module_name, global_name=None, reload=True):
    """
    Import a module.
    :param module_name: Module to import.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: ImportError and ModuleNotFoundError
    """
    if global_name is None:
        global_name = module_name

    if global_name in globals():
        importlib.reload(globals()[global_name])
    else:
        # Attempt to import the module and assign it to globals dictionary. This allow to access the module under
        # the given name, just like the regular import would.
        globals()[global_name] = importlib.import_module(module_name)
    return globals()[global_name]


def install_pip():
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


def install_and_import_module(module_name, package_name=None, global_name=None):
    """
    Installs the package through pip and attempts to import the installed module.
    :param module_name: Module to import.
    :param package_name: (Optional) Name of the package that needs to be installed. If None it is assumed to be equal
       to the module_name.
    :param global_name: (Optional) Name under which the module is imported. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: subprocess.CalledProcessError and ImportError
    """
    if package_name is None:
        package_name = module_name

    if global_name is None:
        global_name = module_name

    # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
    # if a dependency is already installed. This can cause problems if the packages is installed in the user
    # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
    # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
    # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
    # The paths used by pip can be checked with `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

    # Create a copy of the environment variables and modify them for the subprocess call
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", package_name],
        check=True,
        env=environ_copy,
    )

    # The installation succeeded, attempt to import the module again
    import_module(module_name, global_name)


def uninstall_module(module_name, package_name=None, global_name=None):
    """
    Uninstalls the package through pip.
    :param module_name: Module to uninstall.
    :param package_name: (Optional) Name of the package that needs to be uninstalled. If None it is assumed to be equal
       to the module_name.
    :param global_name: (Optional) Name under which the module is uninstalled. If None the module_name will be used.
       This allows to import under a different name with the same effect as e.g. "import numpy as np" where "np" is
       the global_name under which the module can be accessed.
    :raises: subprocess.CalledProcessError and ImportError
    """
    if package_name is None:
        package_name = module_name

    if global_name is None:
        global_name = module_name

    # Blender disables the loading of user site-packages by default. However, pip will still check them to determine
    # if a dependency is already installed. This can cause problems if the packages is installed in the user
    # site-packages and pip deems the requirement satisfied, but Blender cannot import the package from the user
    # site-packages. Hence, the environment variable PYTHONNOUSERSITE is set to disallow pip from checking the user
    # site-packages. If the package is not already installed for Blender's Python interpreter, it will then try to.
    # The paths used by pip can be checked with `subprocess.run([bpy.app.binary_path_python, "-m", "site"], check=True)`

    # Create a copy of the environment variables and modify them for the subprocess call
    environ_copy = dict(os.environ)
    environ_copy["PYTHONNOUSERSITE"] = "1"

    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "--yes", package_name],
        check=True,
        env=environ_copy,
    )


class DEPENDENCY_OT_install_dependencies(bpy.types.Operator):
    bl_idname = f"{addon_name}.install_dependencies"
    bl_label = f"Install {addon_name} dependencies"
    bl_description = (
        "Downloads and installs the required python packages for this add-on. "
        "Internet connection is required. Blender may have to be started with "
        "elevated permissions in order to install the package"
    )
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        # Deactivate when dependencies have been installed
        return True
        return not check_all_dependencies()

    def execute(self, context):
        try:
            install_pip()
            for dep in dependencies:
                install_and_import_module(
                    module_name=dep.module,
                    package_name=dep.package,
                    global_name=dep.name,
                )
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        # TODO Register the panels, operators, etc. since dependencies are installed
        # if opencv is installed, load the rest of the modules
        # campnp = importlib.import_module(".campnp", package=__package__)
        # importlib.reload(campnp)
        # globals()["getsceneinfo"] = getattr(campnp, "getsceneinfo")
        # globals()["solvepnp"] = getattr(campnp, "solvepnp")
        # globals()["camcalib"] = getattr(campnp, "camcalib")

        return {"FINISHED"}


class DEPENDENCY_OT_uninstall_dependencies(bpy.types.Operator):
    bl_idname = f"{addon_name}.uninstall_dependencies"
    bl_label = f"Uninstall {addon_name} dependencies"
    bl_description = (
        "Uninstalls the required python packages for this add-on. "
        "elevated permissions in order to install the package"
    )
    bl_options = {"REGISTER", "INTERNAL"}

    @classmethod
    def poll(cls, context):
        # Deactivate when dependencies have been uninstalled
        return check_all_dependencies()

    def execute(self, context):
        try:
            for dep in dependencies:
                uninstall_module(
                    module_name=dep.module,
                    package_name=dep.package,
                    global_name=dep.name,
                )
                dep.installed = False
        except (subprocess.CalledProcessError, ImportError) as err:
            self.report({"ERROR"}, str(err))
            return {"CANCELLED"}

        # TODO Unregister the panels, operators, etc. since dependencies are uninstalled

        return {"FINISHED"}


def import_dependencies() -> None:
    all_installed = False
    # Try to import dependencies
    try:
        for dep in dependencies:
            import_module(module_name=dep.module, global_name=dep.name)
        all_installed = True
    except ImportError:
        all_installed = False


def dependency_manager_ui(self, context, element=None) -> None:
    # Element is a UI element, such as layout, a row, column, or box.
    if element is None:
        element = self.layout
    box = element.box()

    layout = box

    for dep in dependencies:
        ver = None
        installed = False
        row = layout.row()
        # Check if dependencies are installed

        try:
            ver = importlib.metadata.version(dep.package or dep.module)
            installed = True
        except ImportError:
            ver = None
            installed = False
        if not installed:
            installation_status_msg = (
                f"Dependency Status: {dep.display_name} not found."
            )
        else:
            installation_status_msg = (
                f"Dependency Status: {dep.display_name} {ver} is installed."
            )
        row.label(text=installation_status_msg)

    row = layout.row()
    row.operator(
        DEPENDENCY_OT_install_dependencies.bl_idname,
        text="Install depencies",
        icon="CONSOLE",
    )
    row.operator(
        DEPENDENCY_OT_uninstall_dependencies.bl_idname,
        text="Unistall depencies",
        icon="CONSOLE",
    )


def check_all_dependencies() -> bool:
    """True if all dependencies are installed"""
    all_installed = True

    for dep in dependencies:
        try:
            import_module(module_name=dep.module, global_name=dep.name)
            dep_installed = True
        except ImportError:
            # dependency not installed
            dep_installed = False
        all_installed = all_installed and dep_installed

    return all_installed


manager_classes = (
    DEPENDENCY_OT_install_dependencies,
    DEPENDENCY_OT_uninstall_dependencies,
)

# Use factory to create method to register and unregister the dependency manager classes
register_classes, unregister_classes = bpy.utils.register_classes_factory(
    manager_classes
)


def register():
    register_classes()


def unregister():
    unregister_classes()


# Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
# set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
# of the arguments. DO NOT use this to import other parts of your Python add-on, import them as usual with an
# "import" statement.
dependencies: tuple[Dependency] = (
    Dependency(module="debugpy", display_name="Debugpy"),
)
