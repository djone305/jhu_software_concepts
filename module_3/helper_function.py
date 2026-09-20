# Create a short temporary folder
mkdir C:\tmp

# Point Windows temp variables to this short path
$env:TMP="C:\tmp"
$env:TEMP="C:\tmp"

# Ensure CUDA args are still set
$env:CMAKE_ARGS = "-DGGML_CUDA=on"
$env:FORCE_CMAKE = "1"

# Run the install again
pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir