## File paths

Assume that all repositories use python and uv as the package manager. The python environment is probably stored at the workspace root, `./.venv`, so can be activated with `source ./.venv/bin/activate`. Look into the virtual environment for any information you need from package source code.

The package PXS (pxs) is labelled as `physicsx-pxs`, and therefore will be somewhere like `./.venv/lib/my_python_version/physicsx_pxs`.

In all interactions, be extremely concise and sacrifice grammar for the sake of concision.

If you run into a `zsh: command not found:` error, double check your path (with `echo $PATH`) and make sure you've used `~/.zshenv` to add the proper directories to the path.
