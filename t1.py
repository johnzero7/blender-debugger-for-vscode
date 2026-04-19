import importlib
import os
import pprint
import sys

import bpy

# sys.path.append(
#     r"E:\Repos\blender addons\addons-examples\blender_addon_debugger"
# )

print(f"PATHS: {sys.path}")
print()

print(bpy.context.active_object)
print("Current Working Directory:", os.getcwd())

# print(f"t1 - {bpy.data.filepath = }")
print(f"t1 - {__file__ = }")
print(f"t1 - {__name__ = }")
# print(f"t1 - {sys.path = }")


import t2

importlib.reload(t2)

t2.foo()


print("\n" * 5)


if __name__ == "__main__":
    print("T1 - THIS IS MAIN")
