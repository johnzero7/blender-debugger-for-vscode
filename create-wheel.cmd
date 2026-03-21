-- Create the wheel for debugpy in the ./wheels folder
-- Update for the Python version bundled in Blender intended version
pip download debugpy --python-version=3.13 --dest ./wheels --no-deps
