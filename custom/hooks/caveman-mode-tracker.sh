#!/usr/bin/env bash
# caveman UserPromptSubmit hook (bash port — no node required)
# Reads JSON from stdin, detects /caveman commands, updates flag file.

FLAG_FILE="$HOME/.claude/.caveman-active"

input=$(cat)
prompt=$(echo "$input" | jq -r '.prompt // ""' 2>/dev/null | tr '[:upper:]' '[:lower:]' | xargs)

[ -z "$prompt" ] && exit 0

mode=""

case "$prompt" in
    /caveman-commit*)       mode="commit" ;;
    /caveman-review*)       mode="review" ;;
    /caveman-compress*)     mode="compress" ;;
    "/caveman lite"*)       mode="lite" ;;
    "/caveman ultra"*)      mode="ultra" ;;
    "/caveman wenyan-lite"*) mode="wenyan-lite" ;;
    "/caveman wenyan-ultra"*) mode="wenyan-ultra" ;;
    "/caveman wenyan"*)     mode="wenyan" ;;
    /caveman*)              mode="full" ;;
esac

if [ -n "$mode" ]; then
    mkdir -p "$(dirname "$FLAG_FILE")"
    echo "$mode" > "$FLAG_FILE"
fi

# Deactivation
if echo "$prompt" | grep -qiE '\b(stop caveman|normal mode)\b'; then
    rm -f "$FLAG_FILE"
fi
