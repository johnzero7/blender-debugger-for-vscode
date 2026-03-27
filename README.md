# Why fork?
This fork is for compatibility with the new extension system introduced in Blender 4.2.
This new system allows to bundle dependencies, like debugpy, into the extension to simplify the installation process.

# Blender Addon Debugger for VS Code

## Inspiration / Credits

This project is **based on** [blender-debugger-for-vscode](https://github.com/alanscodelog/blender-debugger-for-vscode), which was **inspired by** [Blender-VScode-Debugger](https://github.com/Barbarbarbarian/Blender-VScode-Debugger).
That project was itself **inspired by** the [remote_debugger.py](https://github.com/sybrenstuvel/random-blender-addons/blob/master/remote_debugger.py) for PyCharm, as explained in the [Blender Developer's Blog post](https://code.blender.org/2015/10/debugging-python-code-with-pycharm/).

# What it does:

- Allows to set breakpoints, and debug installed addons in Blender using VS Code (or any other client using debugpy)
- Check if there is a client attached.

## It doesn't
- Debug Python code from the Blender Text Editor
- It Can't run a script from VS Code into Blender.



![Image Showing VS Code side by side with Blender paused at a breakpoint. In the console, a "Debugger is Attached" Statement is printed.](./images/example.jpg)

# Requirements
- Blender 4.2 or higher
- VS Code

# How to Use

#### Step 1: Install the Extension
Starting with Blender 4.2, extensions support bundled dependencies (including debugpy). All required packages are included in the extension itself, so you don't need any extra setup or configuration. Check Blender docs for more information [https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#bpy-ops-extensions-package-install-files](https://docs.blender.org/manual/en/latest/editors/preferences/extensions.html#bpy-ops-extensions-package-install-files)

#### Step 2: Enable Developer Extras
By default Blender hides developer/debug options.
Go to Edit → Preferences → Interface and enable Developer Extras.
!["Developer Extras" check is located in the Interface menu of the preferences](./images/blender-enable-developer-extras.jpg)

#### Step 3: Locate the Add-on to Debug
You can debug any installed add-on (or create your own). The only requirement is that the add-on must be installed and enabled.

For this guide, we'll use the **Blender Addon Debugger for VS Code** as an example.

Go to **Edit → Preferences → Extensions**, expand **Blender Addon Debugger for VS Code**, and click the **folder icon** next to the path to open the extension's installation folder.
If the addon you are looking for is not here it might be a legacy addon, check in the **Add-ons** tab.
![The extensions Tab show the location of the installed addon](./images/blender-addon-location.jpg)

#### Step 4: Open the folder in VS Code
Open the folder in VS Code.
![This is an example of a launch.json file](./images/vscode-launch.jpg)
Create a launch.json file. Add a configuration for Python Debugger: Remote Attach. The default values for host and port will be enogh. The only thing we need to change is **"remoteRoot"** to the same value of **"localRoot": "${workspaceFolder}"**.

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
                    "remoteRoot": "." //change "." for "${workspaceFolder}" like the line above
                }
            ]
        }
```

#### Step 5: Start debuging
In the menubar click on the Blender icon and open the System menu. The you will find two options.
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
Everyting should be ready to start debugging, try seting a break point in the file **__init__.py**, in the operator **DebugServerStart** place a breakpoint in the first line inside the execute method. Now if you try running that operator in blender the window should freeze and the control should be tranfered to VS Code on the line we set the breakpoint.
![Execution of the operator is halted a the breakpoint](./images/vscode-breakpoint.jpg)


## Note on Downloading

Download from releases the version that corresponds to the version of Blender you are using. If you download or clone the repo you will need to build the package by running **build_releae.py**


## Setting up your scripts

Blender currently has two systems to extend its functionality: Addons (legacy) and Extensions (new system).
Addons and Extensions need to be edited in the location where they are installed in blender.


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
C:\Users\<USER>\AppData\Roaming\Blender Foundation\Blender\4.X\extensions\<repo>
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
      bpy.ops.debug.connect_debugger_vscode(waitForClient=True)

```
See [Application Handlers](https://docs.blender.org/api/current/bpy.app.handlers.html)

### Debugging/Editing Source Code

It is possible to edit the Blender source code but it can be a bit tricky to get it to detect changes (nevermind live editing is buggy anyways).

From blender you can right click just about anything and click "Edit Source" to get it in the text editor. Then to find the path of the file, go to `Text > Save As` and copy it from there.

Open the file in VS Code, connect to the debugging server, make a change and save it.

Now in Blender the text editor will show this little red button in the top left. Click that and reload the file. Then in `Text Editor > Properties` turn on `Live Edit` if you haven't already. Now to actually get Blender to detect any changes you made just type a single character (like add a space anywhere) and *then* it will detect your changes.

# Troubleshooting

- To determine whether the problem is on Blender's side or your editor's: Close Blender and install debugpy this [test script](https://github.com/AlansCodeLog/blender-debugger-for-vscode/blob/master/test.py), you can copy/download it or run it from the addon folder. Run it with Python `python test.py`, and then try to connect to the server with your editor. If you're still getting problems then the problem is with VS Code, try:
    - Check your detected your Python install, or set it manually.
    - For VS Code try reinstalling the VS Code Python extension.


