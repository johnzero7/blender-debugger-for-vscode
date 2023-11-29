'''
Copyright (C) 2018 Alan North
alannorth@gmail.com

Created by Alan North

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
   'name': 'Debugger for VS Code',
   'author': 'Alan North',
   'version': (2, 2, 1),
   'blender': (2, 80, 0), # supports 2.8+ (python 3.7+)
   "description": "Starts debugging server for VS Code.",
   'location': 'In search (Edit > Operator Search) type "Debug"',
   "warning": "Requires installation of dependencies",
   "wiki_url": "https://github.com/AlansCodeLog/blender-debugger-for-vscode",
   "tracker_url": "https://github.com/AlansCodeLog/blender-debugger-for-vscode/issues",
   'category': 'Development',
}

import os
import re
import subprocess
import sys
import sysconfig

import bpy

from .import dependency_manager as dep

NOT_FOUND_MESSAGE = "debugpy not found"


# Declare all modules that this add-on depends on, that may need to be installed. The package and (global) name can be
# set to None, if they are equal to the module name. See import_module and ensure_and_import_module for the explanation
# of the arguments. DO NOT use this to import other parts of your Python add-on, import them as usual with an
# "import" statement.

dep.dependencies = (
    dep.Dependency(module="debugpy"),
)

# pass the globals() to the manager to dinamically import and make the alias available
# to other parts of the code
dep.main_globals = globals()

# Select to manage the instalations of each package separattly or all together
# Default is True
dep.manage_individually = False



# finds path to debugpy if it exists
def check_for_debugpy() -> None | str:

   # 1# Check the platform libraries from
   # Blender embbeded Python’s configuration path
   path = sysconfig.get_path("platlib")
   if path:
      path = os.path.normpath(path)
      if os.path.exists(os.path.join(path, "debugpy")):
         return path

   # 2# check in path just in case PYTHONPATH happens to be set
   # this is not going to work because Blender's sys.path is different
   for path in sys.path:
      path = os.path.normpath(path)
      if os.path.exists(os.path.join(path, "debugpy")):
         return path
      if os.path.exists(os.path.join(path, "site-packages","debugpy")):
         return os.path.join(path, "site-packages")
      if os.path.exists(os.path.join(path, "lib","site-packages","debugpy")):
         return os.path.join(path, "lib","site-packages")

   # 3# Check if debugpy is installed in the runing python (python embedded in Blender)
   pip_info = None
   try:
      pip_info = subprocess.Popen(
         "pip show debugpy",
         shell=True,
         stdout=subprocess.PIPE,
         stderr=subprocess.PIPE
      )
   except Exception as e:
      print(e)

   if pip_info is not None:
      pip_info = str(pip_info.communicate()[0], "utf-8")
      pip_info = pip_info.splitlines()
      #extract path up to last slash
      for match in [x for x in pip_info if "Location: " in x]:
         match = re.search("Location: (.*)", match)
         #normalize slashes
         if match is not None:
            match = match.group(1).rstrip()
            match = os.path.normpath(match)
            if os.path.exists(os.path.join(match, "debugpy")):
               return match

   # 4# search in the system path. python instalations
   checks = [
      ["where", "python"],
      ["whereis", "python"],
      ["which", "python"],
   ]
   location = None
   for command in checks:
      try:
         location = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
         )
      except Exception as e:
         print(e)
         continue

      if location is not None:
         location = str(location.communicate()[0], "utf-8")
         for path in location.splitlines():
            path = os.path.dirname(os.path.normpath(path))
            if os.path.exists(os.path.join(path, "lib","site-packages","debugpy")):
               path = os.path.join(path, "lib","site-packages")
               return path

   return NOT_FOUND_MESSAGE


# Preferences
#########################################################################
class DebuggerPreferences(bpy.types.AddonPreferences):
   bl_idname = __name__

   path: bpy.props.StringProperty(
      name="Location of debugpy (site-packages folder)",
      subtype="DIR_PATH",
      default=check_for_debugpy()
   )

   timeout: bpy.props.IntProperty(
      name="Timeout",
      default=20
   )

   port: bpy.props.IntProperty(
      name="Port",
      min=0,
      max=65535,
      default=5678
   )
   def draw(self, context):
      layout = self.layout

      # add this call to draw the addon preferences
      dep.dependency_manager_ui(self, context, layout)

      if not dep.check_all_dependencies():
         return

      row_path = layout
      row_path.label(text="The addon will try to auto-find the location of debugpy, if no path is found, or you would like to use a different path, set it here.")
      row_path.prop(self, "path")
      row_path.operator(
         DebuggerPathUpdate.bl_idname,
         text="Update Path",
         icon="CONSOLE",
      )

      row_timeout = layout.split()
      row_timeout.prop(self, "timeout")
      row_timeout.label(text="Timeout in seconds for the attach confirmation listener.")

      row_port = layout.split()
      row_port.prop(self, "port")
      row_port.label(text="Port to use. Should match port in VS Code's launch.json.")


# check if debugger has attached
def check_done(i, modal_limit, prefs):
   if i == 0 or i % 60 == 0:
      print(f"Waiting... (on port {prefs.port})")
   if i > modal_limit:
      print("Attach Confirmation Listener Timed Out")
      return {"CANCELLED"}
   if not debugpy.is_client_connected():
      return {"PASS_THROUGH"}
   print('Debugger is Attached')
   return {"FINISHED"}


class DebuggerCheck(bpy.types.Operator):
   bl_idname = "debug.check_for_debugger"
   bl_label = "Debug: Check if VS Code is Attached"
   bl_description = "Starts modal timer that checks if debugger attached until attached or until timeout"

   _timer = None
   count = 0
   modal_limit = 20*60

   # call check_done
   def modal(self, context, event):
      self.count = self.count + 1
      if event.type == "TIMER":
         prefs = bpy.context.preferences.addons[__name__].preferences
         return check_done(self.count, self.modal_limit, prefs)
      return {"PASS_THROUGH"}

   def execute(self, context):
      # set initial variables
      self.count = 0
      prefs = bpy.context.preferences.addons[__name__].preferences
      self.modal_limit = prefs.timeout*60

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
class DebuggerPathUpdate(bpy.types.Operator):
   bl_idname = "debug.update_debugger_path"
   bl_label = "Look for debugger"
   bl_description = "Searches for the location of the debugger"

   def execute(self, context):
      try:
         addon_prefs = bpy.context.preferences.addons[__name__].preferences
         addon_prefs.path = check_for_debugpy()
      except subprocess.CalledProcessError as err:
         self.report({"ERROR"}, str(err))
         return {"CANCELLED"}

      return {"FINISHED"}


class DebugServerStart(bpy.types.Operator):
   bl_idname = "debug.connect_debugger_vscode"
   bl_label = "Debug: Start Debug Server for VS Code"
   bl_description = "Starts debugpy server for debugger to attach to"

   waitForClient: bpy.props.BoolProperty(default=False)

   def execute(self, context):
      # get debugpy and import if exists
      prefs = bpy.context.preferences.addons[__name__].preferences
      debugpy_path = prefs.path
      debugpy_port = prefs.port

      # actually check debugpy is still available
      if debugpy_path == NOT_FOUND_MESSAGE:
         self.report({"ERROR"}, "Couldn't detect debugpy, please specify the path manually in the addon preferences or reload the addon if you installed debugpy after enabling it.")
         return {"CANCELLED"}

      if not os.path.exists(os.path.abspath(os.path.join(debugpy_path, "debugpy"))):
         self.report({"ERROR"}, f"Can't find debugpy at-: {os.path.join(debugpy_path,'debugpy')}.")
         return {"CANCELLED"}

      # if the folder is not in the path, add it to be able to import
      if debugpy_path not in sys.path:
         sys.path.append(debugpy_path)

      global debugpy #so we can do check later
      import debugpy

      # can only be attached once, no way to detach (at least not that I understand?)
      try:
         debugpy.listen(("localhost", debugpy_port))
      except:
         print("Server already running.")

      if (self.waitForClient):
         self.report({"INFO"}, "Blender Debugger for VSCode: Awaiting Connection")
         debugpy.wait_for_client()

      # call our confirmation listener
      bpy.ops.debug.check_for_debugger()
      return {"FINISHED"}


dep.dependant_classes = (
   DebuggerCheck,
   DebugServerStart,
)


preference_classes = (
   DebuggerPreferences,
   DebuggerPathUpdate,
)


register_preference, unregister_preference = bpy.utils.register_classes_factory(
   preference_classes
)


def register():
   register_preference()
   dep.register()


def unregister():
   dep.unregister()
   unregister_preference()


if __name__ == "__main__":
   register()
