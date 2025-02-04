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


# check if debugger has attached
def check_done(i, modal_limit, prefs):
    if i == 0 or i % 60 == 0:
        print(f"Waiting... (on port {prefs.port})")
    if i > modal_limit:
        print("Attach Confirmation Listener Timed Out")
        return {"CANCELLED"}
    if not debugpy.is_client_connected():
        return {"PASS_THROUGH"}
    print("Debugger is Attached")
    return {"FINISHED"}


class DebuggerCheck(bpy.types.Operator):
    bl_idname = "debug.check_for_debugger"
    bl_label = "Debug: Check if VS Code is Attached"
    bl_description = "Starts modal timer that checks if debugger attached until attached or until timeout"

    _timer = None
    count = 0
    modal_limit = 20 * 60

    # call check_done
    def modal(self, context, event):
        self.count = self.count + 1
        if event.type == "TIMER":
            prefs = bpy.context.preferences.addons[__package__].preferences
            return check_done(self.count, self.modal_limit, prefs)
        return {"PASS_THROUGH"}

    def execute(self, context):
        # set initial variables
        self.count = 0
        prefs = bpy.context.preferences.addons[__package__].preferences
        self.modal_limit = prefs.timeout * 60

        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def cancel(self, context):
        print("Debugger Confirmation Cancelled")
        wm = context.window_manager
        wm.event_timer_remove(self._timer)


# Operators
#######################################################################
class DebugServerStart(bpy.types.Operator):
    bl_idname = "debug.connect_debugger_vscode"
    bl_label = "Debug: Start Debug Server for VS Code"
    bl_description = "Starts debugpy server for debugger to attach to"

    waitForClient: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        # get debugpy and import if exists
        prefs = bpy.context.preferences.addons[__package__].preferences
        debugpy_port = prefs.port

        # can only be attached once, no way to detach (at least not that I understand?)
        try:
            debugpy.listen(("localhost", debugpy_port))
        except:
            msg = f"Remote python debugger failed to start (or already started) on port {debugpy_port}."
            self.report({"WARNING"}, msg)
            print(msg)
            return {"CANCELLED"}

        if self.waitForClient:
            self.report({"INFO"}, "Blender Debugger for VSCode: Awaiting Connection")
            debugpy.wait_for_client()

        # call our confirmation listener
        bpy.ops.debug.check_for_debugger()
        return {"FINISHED"}


preference_classes = (
    DebuggerCheck,
    DebugServerStart,
    DebuggerPreferences,
)


register_preference, unregister_preference = bpy.utils.register_classes_factory(
    preference_classes
)


def register():
    register_preference()


def unregister():
    unregister_preference()


if __name__ == "__main__":
    register()
