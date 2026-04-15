# Claude guidelines

Assume all repositories use python and uv. See @skills/uv for full uv usage rules.

The package PXS (pxs) is labelled as `physicsx-pxs`, found at `.venv/lib/<python_version>/site-packages/pxs`.

In all interactions, be extremely concise and sacrifice grammar for the sake of concision.

If you run into a `zsh: command not found:` error, double check your path (with `echo $PATH`) and make sure you've used `~/.zshenv` to add the proper directories to the path.

When quoting code, for example in docstrings, use the single quote style `my_variable` instead of double quote ``my_variable``.

## Rules

- Never `git commit` or `git push`
- Never use an mdash (or --) as a dash when writing text, use a single dash (-).

@claude_md_imports/karpathy-guidelines.md