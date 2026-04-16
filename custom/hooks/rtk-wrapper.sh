#!/usr/bin/env bash
# Wrapper for rtk-rewrite.sh that ensures ~/.local/bin is in PATH.
# Needed on Linux where rtk may be installed there but not in the shell PATH.
export PATH="$HOME/.local/bin:$PATH"
exec bash ~/.claude/hooks/rtk-rewrite.sh
