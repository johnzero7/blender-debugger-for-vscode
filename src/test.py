"""
If you are having problems with making the addon work with your installation of Blender,
you can test if it works outside Blender.

You will need to install debugpy in your current Python environment.

Then run this script from the terminal: "python test.py"
It should print the version of the debugpy module and then stop with the message "Waiting for a client..."

Now, in VS Code, start the "Python Debugger: Remote Attach".
Even if you didn't set any breakpoints, the code should break on the line right under "debugpy.breakpoint()".
If you try to set new breakpoints, they should appear as red dots.
If they are grey, there is something wrong with "localRoot" or "remoteRoot" in the file "launch.json".

Exit the program to terminate the debug server, otherwise it will hold the port.
"""

import debugpy

print(f"debugpy version is: {debugpy.__version__}")
debugpy.listen(("0.0.0.0", 5678))
print(f"is any client listening?: {debugpy.is_client_connected()}")
print("Waiting for a client...")
debugpy.wait_for_client()
print("Client connected!")
debugpy.breakpoint()
print(f"is any client listening?: {debugpy.is_client_connected()}")
print("Ok, bye")
input("press enter to exit")
