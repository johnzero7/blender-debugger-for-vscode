# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 johnzero7
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""
Start a debug server to debug addons and python code in blender
Allows to debug Blender addons and python scripts with the VS Code Debugger using debugpy.
Inspired by: https://github.com/AlansCodeLog/blender-debugger-for-vscode

Notes:
* As of 5/3/2022 debugpy provides no methods to stop the debug server once started.
    The only way to stop it is to close the proccess that intiated it (Blender.exe)
"""

import itertools
import os
import pathlib
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager

import bpy
import debugpy


# Preferences
#########################################################################
class DebuggerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    host: bpy.props.StringProperty(
        name="Host",
        default="127.0.0.1",
        description="Remote host to accept connections. If 0.0.0.0 will accept connections from any host. Should match host in VS Code's launch.json",
    )

    port: bpy.props.IntProperty(
        name="Port",
        min=1024,
        max=65535,
        default=5678,
        description="Port to use. Should match port in VS Code's launch.json",
    )

    timeout: bpy.props.IntProperty(
        name="Timeout",
        default=20,
        description="Timeout in seconds for the attach confirmation listener.",
    )

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
        layout.prop(self, "host")
        layout.prop(self, "port")
        layout.prop(self, "timeout")


# Operators
#########################################################################
class DebuggerCheck(bpy.types.Operator):
    """
    Poll for a cliente conection until:
    - Succesfull client connection
    - Timeout
    """

    bl_idname = "debug.check_for_debugger"
    bl_label = "Debug: Check if Client is Attached"
    bl_description = "Starts modal timer that checks if debugger attached until attached or until timeout"

    def modal(self, context, event):
        if event.type == "TIMER":
            prefs = bpy.context.preferences.addons[__package__].preferences
            now = time.time()
            time_diff = now - self._start_time

            remaining_seconds = prefs.timeout - time_diff
            clear_line = "\033[K"

            # Print activity message
            console_text = f"\r{next(self._spinner)} Waiting for connection on port: {prefs.port} (Timeout: {int(remaining_seconds)+1}{clear_line})"
            sys.stdout.write(console_text)
            sys.stdout.flush()

            # Connected
            if debugpy.is_client_connected():
                msg = "Debugpy client connected!"
                self.report({"INFO"}, msg)
                print()
                print(f"{msg}")
                self.cleaunp(context)
                return {"FINISHED"}

            # Timeout
            if time_diff > prefs.timeout:
                msg = f"Debugpy attach timeout after {prefs.timeout} seconds"
                self.report({"WARNING"}, msg)
                print()
                print(f"{msg}")
                self.cleaunp(context)
                return {"CANCELLED"}

        # To not block other interacion with blender
        return {"PASS_THROUGH"}

    def execute(self, context):
        # set initial variables
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)

        spinner_frames = ["⠏", "⠛", "⠹", "⢸", "⣰", "⣤", "⣆", "⡇"]
        self._spinner = itertools.cycle(spinner_frames)
        self._start_time = time.time()
        return {"RUNNING_MODAL"}

    def cleaunp(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

    def cancel(self, context):
        msg = "Debugpy wait → cancelled"
        self.report({"INFO"}, msg)
        print(msg)
        self.cleaunp(context)


class DebugServerStart(bpy.types.Operator):
    """
    Initialize the debug server then poll for a client connection
    """

    bl_idname = "debug.connect_debugger_vscode"
    bl_label = "Debug: Start Debug Server"
    bl_description = "Starts debugpy server for debugger to attach to"

    waitForClient: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        debugpy_host, debugpy_port = prefs.host, prefs.port

        # can only be attached once, no way to detach (at least not that I understand?)
        try:
            debugpy.listen((debugpy_host, debugpy_port))
        except RuntimeError as e:
            # Usually means already listening
            msg = f"debugpy already listening on port {debugpy_port} or failed: {e}"
            self.report({"WARNING"}, msg)
            print(msg)
            return {"CANCELLED"}
        except Exception as e:
            msg = f"debugpy listen failed: {e}"
            self.report({"ERROR"}, msg)
            print(msg)
            return {"CANCELLED"}

        if self.waitForClient:
            self.report({"INFO"}, "Blender Debugger for VS Code: Awaiting Connection")
            debugpy.wait_for_client()

        # call our confirmation listener
        bpy.ops.debug.check_for_debugger()
        return {"FINISHED"}


@contextmanager
def run_in_context(script_path: str | os.PathLike[str]) -> Iterator[None]:
    """
    Context manager that sets up the environment to run a standalone script as if
    it were executed directly (via `python script.py`), but in blender.

    Changes made (and then restored):
        - Current working directory → script's parent directory
        - sys.path → script's parent directory is inserted at the front
        - sys.dont_write_bytecode = True (prevents .pyc file generation)

    Also it undoes changes made by the scripts
        - Unload modules imported in the scripts to prebent side effects
        - delete created globals
    """
    script_dir = str(pathlib.Path(script_path).parent)

    # Preserve previous values
    original_cwd: str = os.getcwd()
    original_sys_path: list[str] = sys.path.copy()
    original_dont_write_bytecode: bool = (
        sys.dont_write_bytecode
    )  # prevent writing __pycache__
    # Keep track of originally loaded modules to prevent side effects from imports in the script
    original_modules = list(sys.modules.keys())
    original_globals = list(globals().keys())

    try:
        os.chdir(script_dir)
        sys.path.insert(0, script_dir)  # Important: insert at front
        sys.dont_write_bytecode = True

        yield

    finally:
        # Restore previous values
        os.chdir(original_cwd)
        sys.path[:] = original_sys_path
        sys.dont_write_bytecode = original_dont_write_bytecode
        # remove all modules that were imported during the script execution to prevent side effects
        for name in list(sys.modules.keys()):
            if name not in original_modules:
                sys.modules.pop(name, None)
        for name in list(globals().keys()):
            if name not in original_globals:
                globals().pop(name, None)


class TEXT_OT_debug_run(bpy.types.Operator):
    """Run the current text as a script compatible with the VS Code Debugger"""

    bl_idname = "text.debug_run"
    bl_label = "Debug"
    bl_description = "Run the current script (Debug mode)"
    bl_options = {"REGISTER"}

    def execute(self, context):
        # Get the current text editor
        text = context.space_data.text

        if not text:
            self.report({"ERROR"}, "No text block to run")
            return {"CANCELLED"}

        if text.is_in_memory:
            self.report({"ERROR"}, "Cannot run internal text blocks in debug mode")
            return {"CANCELLED"}

        filepath = pathlib.Path(text.filepath)

        if not filepath.is_file():
            self.report(
                {"ERROR"},
                "The current text block must be saved to a file to run in debug mode",
            )
            return {"CANCELLED"}

        if not filepath.exists():
            self.report(
                {"ERROR"},
                "The current text block must be saved to a file to run in debug mode",
            )
            return {"CANCELLED"}

        try:
            global_namespace = {
                "__file__": str(filepath),
                "__name__": "__main__",
            }
            with run_in_context(filepath):
                # Work from the version saved on disk
                with open(filepath, "r") as file:
                    exec(
                        compile(file.read(), filepath, "exec"),
                        globals=global_namespace,
                    )

            self.report({"INFO"}, f"Script executed: {filepath.name}")
            return {"FINISHED"}

        except Exception as e:
            # Show the error in the Info window and console
            self.report({"ERROR"}, f"Error running script: {e}")
            print(f"--- Debug Run Error in {text.name} ---")
            import traceback

            traceback.print_exc()
            return {"CANCELLED"}


# Draw the main menu entry for:
#   {Blender Icon} -> System -> Debug: Start Debug Server
#                             + Debug: Check if Client is Attached
def draw_python_debugger_blender_system_menu(self, context):
    if bpy.context.preferences.view.show_developer_ui:
        self.layout.separator(factor=1.0)
        self.layout.operator(DebugServerStart.bl_idname, icon="SCRIPT")
        self.layout.operator(DebuggerCheck.bl_idname, icon="SCRIPT")


def draw_python_debugger_text_editor_menu(self, context):
    """Draw function that gets appended to the Text Editor header"""
    layout = self.layout

    # This adds a separator so the button appears nicely after "Run Script"
    layout.separator(factor=1.0)

    # The button with bug icon
    layout.operator(
        TEXT_OT_debug_run.bl_idname,
        text="Debug",
        icon="FILE_SCRIPT",
    )


# Registration
#########################################################################
_classes = (
    DebuggerCheck,
    DebugServerStart,
    DebuggerPreferences,
    TEXT_OT_debug_run,
)


_register, _unregister = bpy.utils.register_classes_factory(_classes)


def register():
    _register()
    bpy.types.TOPBAR_MT_blender_system.append(draw_python_debugger_blender_system_menu)
    bpy.types.TEXT_HT_header.append(draw_python_debugger_text_editor_menu)


def unregister():
    bpy.types.TOPBAR_MT_blender_system.remove(draw_python_debugger_blender_system_menu)
    bpy.types.TEXT_HT_header.remove(draw_python_debugger_text_editor_menu)
    _unregister()


if __name__ == "__main__":
    register()
