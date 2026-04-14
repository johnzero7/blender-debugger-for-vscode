# Why fork?
This fork is for compatibility with the new extension system introduced in Blender 4.2.
This new system allows to bundle dependencies, like debugpy, into the extension package to simplify the installation process.

# Blender Python Debugger
![Image Showing VS Code side by side with Blender paused at a breakpoint. In the console, a "Debugger is Attached" Statement is printed.](./images/example.jpg)

## Inspiration / Credits

[Blender Python Addon Debugger for VS Code](https://github.com/johnzero7/blender-python-debugger) is **based on** [blender-debugger-for-vscode](https://github.com/alanscodelog/blender-debugger-for-vscode), which was **inspired by** [Blender-VScode-Debugger](https://github.com/Barbarbarbarian/Blender-VScode-Debugger).
That project was itself **inspired by** the [remote_debugger.py](https://github.com/sybrenstuvel/random-blender-addons/blob/master/remote_debugger.py) for PyCharm, as explained in the [Blender Developer's Blog post](https://code.blender.org/2015/10/debugging-python-code-with-pycharm/).

# What it does:
This addon allows the user to debug python code of installed addons and standalone python scripts in the **Blender Text Editor**
- Allows to set breakpoints, and debug installed addons in Blender using VS Code (or any other client implementing the Debug Protocal Adapted, DAP, like VS Code, Pycharm, Zed, etc )
- Check if there is a client attached.

## It doesn't
- It doesn't run python scripts from and IDE into Blender.


# Requirements
- Blender 4.2 or higher
- An IDE with DAP support (VS Code, Pycharm, Zed, etc)

# How to Use

#### Step 1: Install the Extension
Starting with Blender 4.2, extensions support bundled dependencies (including debugpy). All required packages are included in the extension itself, so you don't need any extra setup or configuration. Check Blender docs for more information [https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#bpy-ops-extensions-package-install-files](https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#bpy-ops-extensions-package-install-files)

#### Step 2: Enable Developer Extras
By default Blender hides developer/debug options.
Go to Edit → Preferences → Interface and enable Developer Extras.
!["Developer Extras" check is located in the Interface menu of the preferences](./images/blender-enable-developer-extras.jpg)

#### Step 3: Locate the Add-on/Script to Debug
You can debug any installed add-on (or create your own). The only requirement is that the add-on must be installed and enabled.

For this guide, we'll use the **Blender Addon Debugger** as an example.

Go to **Edit → Preferences → Extensions**, expand **Blender Addon Debugger**, and click the **folder icon** next to the path to open the extension's installation folder.
If the addon you are looking for is not here it might be a legacy addon, check in the **Add-ons** tab.
![The extensions Tab show the location of the installed addon](./images/blender-addon-location.jpg)
For standalone scripts the sctipt needs to be in a folder accesible by blender so it can be opened in the Text Editor.

Now we will use VS Code for this example

#### Step 4: Open the folder in VS Code
Open the **folder** with the source in VS Code.
![This is an example of a launch.json file](./images/vscode-launch.jpg)
Create a launch.json file. Add a configuration for Python Debugger: Remote Attach. The default values for host and port will be enough. The only thing we need to change is **"remoteRoot"** to the same value of **"localRoot": "${workspaceFolder}"**.

```JSON
        {
            "name": "Python Debugger: Remote Attach",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678 //select the same port in blender addon preferences
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}",
                    "remoteRoot": "." //change "." to "${workspaceFolder}" like the line above
                }
            ]
        }
```

#### Step 5: Start the debug server
In Blender go to the menubar and click on the Blender icon and open the System menu. The you will find two options (These can also be found in the search menu.)
- **Debug: Start Debug Server**
: Starts the debug server on the selected port and wait for a connection.
- **Debug: Check if Client is Attached**
: Check if the is a client attached to the process until a connection is made or until the timeout is reached.

Notes:
* The debug server can only be started once and remains running after that.
* As of 5/3/2022 debugpy provides no methods to stop the debug server. The only way to stop it is to close the proccess that intiated it (Blender.exe)

![Open the blender Icon => System => Debug](./images/blender-start-server.jpg)
![Use the search tool to find the debug tools](./images/blender-search.jpg)

#### Step 6: Attach VS Code to the remote server
Now that the remote server is running we can establish a connection from VS Code. Go to VS Code, in the **Run & Debug** Tab select **Python Debugger: Remote Attach** and click the green Arrow or press F5.

#### Step 7: Set Breakpoints and start debugging
Everyting should be ready to start debugging, try seting a break point in the file `__init__.py`, in the operator **DebugServerStart** place a breakpoint in the first line inside the execute method. Now if you try running that operator in blender the window should freeze and the control should be tranfered to VS Code on the line we set the breakpoint.
![Execution of the operator is halted a the breakpoint](./images/vscode-breakpoint.jpg)


## Setting up your scripts

Blender currently has two systems to extend its functionality: Addons (legacy) and Extensions (new system).
Addons and Extensions need to be edited in the location where they are installed in Blender.


### Addons (legacy)

The default folder for addons is:
```
C:\Users\<USER>\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons
```
You can create a custom folder addons.
In Blender go to: `Edit > Preferences > File Paths > Script Directories` and add the path to the folder you're going to develop your addon in (e.g: "C:\Code\Blender Stuff").
The folder structure must be the same than in the default addon folder. In this example:

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
All addons mus be inside the forlder **addons** or blender will not find them, but in the File Path configuration do not include it.

See [Blender Docs => Installing Add-ons => User-Defined Add-on Path](https://docs.blender.org/manual/en/latest/editors/preferences/addons.html#:~:text=Add%20a%20subdirectory%20under%20my_scripts%20called%20addons%20(it%20must%20have%20this%20name%20for%20Blender%20to%20recognize%20it) for details.

You can install from blender or copy the addon folder to the new location.


### Extensions (new system)

The default folder for extensions is:
```
C:\Users\<USER>\AppData\Roaming\Blender Foundation\Blender\4.2\extensions\<repo>
```

To add a custom folder for Extensions
`Edit > Preferences > Get Extensions > Repositories > + > Add Local Repository`

Set a name for the new repository "MyExtensions", check custom folder and set the new path (e.g: "C:\Code\Blender Stuff\extensions")
The folder structure must be the same than in the default local extension repository. In this example:

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


### Standalone scripts
You can debug standalone scripts running then from the text editor using the button **Debug**
![Run stand alone scripts from the text editor](./images/blender-text-editor.jpg)


# Useful tips
### Editing while debuging
Note though that if you make changes to the addon files, Blender will not detect them. Have to go to Sysyem => Reload Scripts or open up Blender's search and type `Reload Scripts` (bpy.ops.script.reload()) when you make changes. But if there is a change in a submodule that the addon is importing even this will not work. The reason is Python does not re-import modules already imported, you will need to use dinamic imports using importlib.reload(my_module) or restart blender.

### Blender Python API
You might enconter the issue that VS Code marks with error things like `import bpy` and does not provide auto comple for blender functionality. This is because `bpy` is not a real python module, it's an API to provide Python access to Blender C/C++ code. For this reason you will not be able to run python code that imports bpy outside of Blender.
But, to fix the import errors and provide autocompletion we can install a [fake-bpy-module](https://pypi.org/project/fake-bpy-module)

## Advanced Usage

### Wait for Client

The debugger can be made to wait for a client to connect (this will pause all execution). This can be useful for debugging the connection or when running blender headless / in background mode.

To do so, call the server connect command from the python console or from a script/addon like so:

```python
bpy.ops.debug.connect_debugger_vscode(waitForClient=True)
```

#### Running in Headless Mode

First make sure the addon is installed, enabled, and works when you run blender normally.

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

You can't live edit the code, but you can update and appply changes to the code.

For stand alone scripts you can edit the code clicking the button "Debug" in the text editor.
All changes saved to disk will be executed.

For Addons you will need to force Blender to reload the python code.
In the menubar click on the Blender icon, select 'System > Reload Scripts' (or same name in the search tool)
This will make Blender reload all python code.
But ther is a problem, modules previously imported will not be updated. This is a feature of Python to prevent reload modules already loaded.
To circunvent this you will need to programatically reimport the module using the importlib module.

For example if you imported the module mymodule like this
```
import mymodule
```
you will need to dinamically force reloading the module

```
import sys
import importlib

if 'mymodule' in sys.modules:
    importlib.reload(mymodule)
import mymodule

```
You only need to reload modules if you modify the code.


# Troubleshooting

- To determine whether the problem is on Blender's side or your editor's: Close Blender and install
debugpy this [test script](https://github.com/AlansCodeLog/blender-debugger-for-vscode/blob/master/test.py),
you can copy/download it or run it from the addon folder. Run it with Python `python test.py`,
and then try to connect to the server with your editor.

# Notes About IDEs
In some IDEs, like Pycharm, when you stop/rerun the cliente connection it also kills
the subprocess running the debug server.
As a consecuence you will not be able to reconnect to the remote server, because the subprocess is dead.
And you will not be able to start a new remote server because internal flags still think the subproccess exists.
In some cases it will even kill the Blender process. So be careful to not stop/rerun the the connection.
The only solution for now is to restart Blender.

VS Code is the only one I tested that works well and does not kill the process or subprocess when stoping or restarting the connection.


# Note on Downloading

Download from releases the version that corresponds to the version and platform of Blender you are using.
If you download or clone the repo you will need to build the package by running **build_releae.py**.
This will download the dependencies (debugpy) and generate a package for each platform available.


