"""
This blender extension allows IDEs to debug Blender python code using debugpy,
a implementation of the Debug Adapter Protocol (DAP) specifically for Python

If you are having problems with making the addon work with your installation of Blender,
you can test if it works outside Blender.

You will need to install debugpy in your current Python environment.

Then run this script from the terminal: "python test.py"
It should print the version of the debugpy module and then stop with the message "Waiting for a client..."

Now in VS Code, or any other IDE that supports debugpy, start the "Python Debugger: Remote Attach".
Even if you didn't set any breakpoints, the code should break on the line right under "debugpy.breakpoint()".
If you try to set new breakpoints, but they appear greyed out, there is something wrong with "localRoot" or "remoteRoot" in the file "launch.json".
If the they appear as red dots you are all set to go and debug you Python code in blender.

Exit the program to terminate the debug server, otherwise it will hold the port.
"""

import debugpy

print(f"debugpy version is: {debugpy.__version__}")
debugpy.listen(("127.0.0.1", 5678))
print(f"is any client listening?: {debugpy.is_client_connected()}")
print("Waiting for a client...")
debugpy.wait_for_client()  # stop execution until a client makes a connecttion to the debug server
print("Client connected!")
debugpy.breakpoint()  # programatically set a breakpoint
print(f"is any client listening?: {debugpy.is_client_connected()}")
print("Ok, bye")
input("press enter to exit")
