# Why fork?
This fork is for compatibility with the new extension system introduced in Blender 4.2.
This new system allows to bundle dependencies, like debugpy, into the extension package to simplify the installation process.

# Blender Python Debugger
![Image Showing VS Code side by side with Blender paused at a breakpoint. In the console, a "Debugger is Attached" Statement is printed.](./images/example.jpg)

## Inspiration / Credits

[Blender Python Addon Debugger for VS Code](https://github.com/johnzero7/blender-python-debugger) is **based on** [blender-debugger-for-vscode](https://github.com/alanscodelog/blender-debugger-for-vscode), which was **inspired by** [Blender-VScode-Debugger](https://github.com/Barbarbarbarian/Blender-VScode-Debugger).
That project was itself **inspired by** the [remote_debugger.py](https://github.com/sybrenstuvel/random-blender-addons/blob/master/remote_debugger.py) for PyCharm, as explained in the [Blender Developer's Blog post](https://code.blender.org/2015/10/debugging-python-code-with-pycharm/).

# What it does:

This addon enables debugging of Python code in Blender using external debuggers that implement the Debug Adapter Protocol (DAP) like VS Code, PyCharm, or Zed. You can:
- Debug installed addons
- Debug standalone Python scripts
- Debug Blender Python source code
- Set breakpoints and step through Blender addon and script code
- Check if a debugger client is attached to the Blender process

## Limitations

- Does not execute Python scripts from an IDE directly into Blender (you must run them from Blender's Text Editor or as addon operators)


# Requirements

- **Blender 4.2** or higher (this addon relies on the new extension system)
- **An IDE with DAP support** like VS Code, PyCharm, Zed, or similar
- **Python debugger**: debugpy (bundled with the extension, no separate installation needed)

# How to Use

#### Step 1: Install the Extension
Go to releases an download the package for your version of Blender and platform.
Starting with Blender 4.2, extensions support bundled dependencies. All required packages are included in the extension itself, so you don't need any extra setup or configuration. Check Blender docs for more information [https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#bpy-ops-extensions-package-install-files](https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#bpy-ops-extensions-package-install-files)

#### Step 2: Enable Developer Extras
By default Blender hides developer/debug options.
Go to Edit → Preferences → Interface and enable Developer Extras.
!["Developer Extras" check is located in the Interface menu of the preferences](./images/blender-enable-developer-extras.jpg)

#### Step 3: Locate the Add-on/Script to Debug

You can debug any installed add-on, standalone script or even the Blender Python source code.
We just need the folder where the Python code resides.

For this guide, we'll use the **Blender Addon Debugger** and VS Code as an example.


**For Extensions (Blender 4.2+):**
Go to **Edit → Preferences → Extensions**, expand **Blender Addon Debugger**, and click the **folder icon** to open the extension's installation folder.
![The extensions Tab show the location of the installed addon](./images/blender-addon-location.jpg)

**For Legacy Addons:**
If you're using an older addon, check the **Add-ons** tab under preferences.

**For Standalone Scripts:**
The script must be in a folder that Blender can access so it can be opened in the Text Editor.

**For Blender Python Source code:**
Locate the Blender Installation folder (where Blender.exe resides). Open the folder for the current Blender version.

#### Step 4: Open the folder in VS Code
Open the **folder** with the source in VS Code, then create a `launch.json` file in the `.vscode` folder (create the folder if it doesn't exist).

Add a configuration for "Python Debugger: Remote Attach". The default values for host and port are fine, but you must change **"remoteRoot"** to match **"localRoot"**. Both should point to the same directory.
![This is an example of a launch.json file](./images/vscode-launch.jpg)
```json
{
    "name": "Python Debugger: Remote Attach",
    "type": "debugpy",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    },
    "pathMappings": [
        {
            "localRoot": "${workspaceFolder}",
            "remoteRoot": "${workspaceFolder}"
        }
    ]
}
```

Key settings:
- **host**: "localhost" (Blender is running on your local machine)
- **port**: 5678 (must match the port in Blender's addon preferences)
- **localRoot**: Your project folder in VS Code
- **remoteRoot**: The same path where Blender finds your project

#### Step 5: Start the debug server
In Blender go to the menubar and click on the Blender icon and open the System menu. Then you will find two options (These can also be found in the search menu.)
- **Debug: Start Debug Server**
: Starts the debug server on the selected port and waits for a connection.
- **Debug: Check if Client is Attached**
: Check if there is a client attached to the process until a connection is made or until the timeout is reached.

Notes:
* The debug server can only be started once and remains running after that.
* As of 5/3/2022 debugpy provides no methods to stop the debug server. The only way to stop it is to close the process that initiated it (Blender.exe)

![Open the Blender Icon => System => Debug](./images/blender-start-server.jpg)
![Use the search tool to find the debug tools](./images/blender-search.jpg)

#### Step 6: Attach VS Code to the remote server
Now that the remote server is running we can establish a connection from VS Code. Go to VS Code, in the **Run & Debug** Tab select **Python Debugger: Remote Attach** and click the green Arrow or press F5.

#### Step 7: Set Breakpoints and start debugging
Everything should be ready to start debugging. Try setting a breakpoint in the file `__init__.py`, in the operator **DebugServerStart** place a breakpoint on the first line inside the execute method. Now if you try running that operator in Blender the window should freeze and control should be transferred to VS Code on the line where you set the breakpoint.
![Execution of the operator is halted a the breakpoint](./images/vscode-breakpoint.jpg)


## Setting up your scripts

Blender currently has two systems to extend its functionality: Addons (legacy) and Extensions (new system).
Addons and Extensions need to be edited in the location where they are installed in Blender.


### Addons (legacy)

The default folder for addons is:
```
C:\Users\<USER>\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons
```
You can create a custom folder for addons. In Blender, go to: `Edit > Preferences > File Paths > Script Directories` and add the path to your development folder (e.g: "C:\Code\Blender Stuff").


```
...
└── Blender Stuff
    └── addons       <-- *Important*
        ├── your-addon-folder
            ├── __init__.py
            ├── ...etc
        ├── another-addon
        ├── ...
```
Important: The folder structure must have an **addons** subfolder inside it. Blender will not recognize addons in the root folder, they must be inside the subfolder named "addons". In the File Paths configuration, do not include "addons" in the path.

See [Blender Docs => Installing Add-ons => User-Defined Add-on Path](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html#:~:text=Add%20a%20subdirectory%20under%20my_scripts%20called%20addons%20(it%20must%20have%20this%20name%20for%20Blender%20to%20recognize%20it) for details.

You can install from blender or copy the addon folder to the new location.


### Extensions (new system)

The default folder for extensions is:
```
C:\Users\<USER>\AppData\Roaming\Blender Foundation\Blender\4.2\extensions\<repo>
```

To add a custom folder for Extensions, go to:
`Edit > Preferences > Get Extensions > Repositories > + > Add Local Repository`

Set a name for the new repository (e.g., "MyExtensions"), check "custom folder", and set the path (e.g: "C:\Code\Blender Stuff\extensions").
The folder structure must be the same as in the default local extension repository. In this example:

```
...
└── Blender Stuff
    └── extensions
        ├── your-extension-folder
            ├── __init__.py
            ├── blender_manifest.toml
            ├── ...etc
        ├── another-addon
        ├── ...
```

https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#installing-extensions

Blender does not support duplicated addons/extensions. If you have multiple copies installed in different folders uninstall them until only one is left.


### Standalone Scripts

You can debug standalone Python scripts by running them from Blender's Text Editor. Open the script in the Text Editor and click the **Debug** button to execute it with the debugger attached.
![Run stand alone scripts from the text editor](./images/blender-text-editor.jpg)

# Useful tips
### Editing while debugging

If you modify addon files while the debugger is running, Blender won't automatically detect the changes. You must manually reload the scripts:

1. Go to **System → Reload Scripts** in the Blender menu (or search for "Reload Scripts" with the search tool).
2. This will reload all Python code that Blender has imported.

**Important Note:** Python doesn't re-import modules that are already loaded. This is a feature of Python. If you modify a submodule, reloading scripts won't update it. To force a reload of specific modules, use `importlib.reload()` in your code, or restart Blender entirely.

### Blender Python API
You might encounter VS Code errors for `import bpy` and lack of autocompletion for Blender functions. This happens because `bpy` is not a standard Python module—it's an API providing Python access to Blender's C/C++ code. You cannot run Python code that imports `bpy` outside of Blender.

To resolve this, install the [fake-bpy-module](https://pypi.org/project/fake-bpy-module) package. This provides type hints and autocompletion for the Blender API.

## Advanced Usage

### Wait for Debugger Client

By default, the debug server starts immediately and listens for a client connection. However, you can make the server wait for a client to connect before continuing execution. This is useful for debugging startup code or when running Blender in headless mode.

To enable this, call:

```python
bpy.ops.debug.connect_debugger_vscode(waitForClient=True)
```

#### Running in Headless Mode

First make sure the addon is installed, enabled, and works when you run Blender normally.

Blender can then be run in background mode with the `-b/--background` switch (e.g. `blender --background`, `blender --background --python your_script.py`).

See [Blender Command Line](https://docs.blender.org/manual/en/latest/advanced/command_line/introduction.html).

You can detect when blender is run in background/headless mode and make the debugger pause and wait for a connection in your script/addon:

```python
if bpy.app.background:
	bpy.ops.debug.connect_debugger_vscode(waitForClient=True)
```

This will wait for a connection to be made to the debugging server. Once this is established, the script will continue executing and VS Code should pause on breakpoints that have been triggered.

For addons, you will need to do this from a handler:

```python
from bpy.app.handlers import persistent
#...
def register():
   bpy.app.handlers.load_post.append(load_handler)
#...
@persistent
def load_handler(dummy):
	# remove handler so it only runs once
   bpy.app.handlers.load_post.remove(load_handler)
   if bpy.app.background:
      bpy.ops.debug.connect_debugger(waitForClient=True)

```
See [Application Handlers](https://docs.blender.org/api/current/bpy.app.handlers.html)

### Editing Source Code while debugging

**For Standalone Scripts:**
Edit the code, only the changes saved to disk will have effect, then click the **Debug** button to run the script.


**For Addons:**
You must force Blender to reload the Python code:
In the menu, click the Blender icon and select **System → Reload Scripts** (or search for "Reload Scripts"). This reloads all Python code.

Python doesn't automatically re-import modules that are already loaded. If you've modified a module that other code imports, you need to manually reload it:

Example:

```
import sys
import importlib

if 'mymodule' in sys.modules:
    importlib.reload(mymodule)
import mymodule

```
You only need to reload modules if you modify the code.


# Troubleshooting

- To determine whether the problem is on Blender's side or on the editor's side: Close Blender, install debugpy manually in the Python environment, and run this [test script](https://github.com/AlansCodeLog/blender-debugger-for-vscode/blob/master/test.py). You can copy/download it or run it from the addon folder. Execute it with `python test.py` and then try to connect to the server with your editor.

# Notes About IDEs
In some IDEs, like PyCharm, when you stop/rerun the client connection it also kills
the subprocess running the debug server.
As a consequence you will not be able to reconnect to the remote server, because the subprocess is dead.
And you will not be able to start a new remote server because internal flags still think the subprocess exists.
In some cases it will even kill the Blender process. So be careful not to stop/rerun the connection.
The only solution for now is to restart Blender.

Of all the IDEs I tested, VS Code reliably maintains the connection and does not kill the debug server process when stopping or restarting the debugger.


# Downloading and Building

Download the appropriate version from the releases page for your Blender version and platform.

If you download or clone the repository, you will need to build the package by running **build_release.py**. This script downloads the dependencies (debugpy) and generates platform-specific packages.


