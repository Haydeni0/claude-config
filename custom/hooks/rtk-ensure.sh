#!/usr/bin/env bash
if ! command -v rtk &>/dev/null && ! [ -x "$HOME/.local/bin/rtk" ]; then
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"RTK is not installed. Install it (no root needed) by running: curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh\nThen run: rtk init -g --auto-patch to wire up the Claude Code hook."}}'
fi
exit 0
