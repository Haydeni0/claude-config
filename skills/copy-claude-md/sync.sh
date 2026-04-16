#!/bin/bash
{
  printf -- '---\nalwaysApply: true\n---\n\n'
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^@(.+)$ ]]; then
      ref="${BASH_REMATCH[1]// /}"
      filepath="$HOME/.claude/$ref"
      if [ -f "$filepath" ]; then
        echo ""
        cat "$filepath"
        echo ""
      else
        echo "$line"
      fi
    else
      echo "$line"
    fi
  done < "$HOME/.claude/CLAUDE.md"
} | pbcopy
echo "Copied. Paste into: Cursor Settings > General > Rules for AI"
