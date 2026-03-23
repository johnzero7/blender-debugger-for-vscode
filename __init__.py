import itertools
import sys
import time

import bpy
import debugpy


# Preferences
#########################################################################
class DebuggerPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    timeout: bpy.props.IntProperty(
        name="Timeout",
        default=20,
        description="Timeout in seconds for the attach confirmation listener.",
    )

    port: bpy.props.IntProperty(
        name="Port",
        min=1024,
        max=65535,
        default=5678,
        description="Port to use. Should match port in VS Code's launch.json",
    )

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True
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
    bl_label = "Debug: Check if VS Code is Attached"
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
    bl_label = "Debug: Start Debug Server for VS Code"
    bl_description = "Starts debugpy server for debugger to attach to"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        debugpy_port = prefs.port

        # can only be attached once, no way to detach (at least not that I understand?)
        try:
            debugpy.listen(("localhost", debugpy_port))
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

        # call our confirmation listener
        bpy.ops.debug.check_for_debugger()
        return {"FINISHED"}


# Registration
#########################################################################
classes = (
    DebuggerCheck,
    DebugServerStart,
    DebuggerPreferences,
)


_register, _unregister = bpy.utils.register_classes_factory(classes)


def register():
    _register()


def unregister():
    _unregister()


if __name__ == "__main__":
    register()
