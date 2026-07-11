#!/usr/bin/env bash
# sync.sh — make this machine match ~/.claude (the single source of truth).
#
# Runs settings-sync (template -> derived opencode/pi files), then materializes
# the machine-local installs the repo declares: pi packages (pinned in
# pi/settings.json#packages[]) and the evo plugin for claude-code/opencode.
#
# Idempotent; safe to re-run. Manual invocation:
#   bash ~/.claude/sync.sh
#
# Prereqs: uv <https://docs.astral.sh/uv/>, jq, and the host CLIs you use
# (pi, claude, opencode). Hosts not on PATH are skipped silently.
#
# pi installs always target ~/.pi/agent (pi's default home, the source glm-pi
# copies from); PI_CODING_AGENT_DIR is unset so a glm-pi shell doesn't redirect
# installs to its throwaway /tmp runtime dir.
#
# Check-if-missing: pi packages are checked by probing ~/.pi/agent/npm/node_modules/<name>
# (the actual install location; `pi list` only reads the settings.json declaration,
# not the filesystem, so it can't tell installed-vs-declared). evo per-host installs
# are checked via a filesystem probe of their known cache path. PI_CODING_AGENT_DIR
# is unset so both checks resolve pi's default home regardless of launch shell.
# `pi install` / `evo install` are idempotent fallbacks. Nothing present is ever
# incorrectly skipped.

set -uo pipefail

# Always target pi's default agent dir (~/.pi/agent), the source glm-pi copies
# from at launch. If sync.sh runs inside a glm-pi shell, PI_CODING_AGENT_DIR is
# set to a throwaway /tmp runtime; unsetting it makes pi install/list read the
# real home so packages survive glm-pi runtime rebuilds and work for plain pi too.
unset PI_CODING_AGENT_DIR

CLAUDE_DIR="${CLAUDE_DIR:-$HOME/.claude}"
exit_code=0

log()  { echo "sync: $*"; }
warn() { echo "sync: warn: $*" >&2; exit_code=1; }

# --- 1. uv (hard prereq; everything depends on it) ---
if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv not found. Install: https://docs.astral.sh/uv/" >&2
  echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

# --- 2. settings-sync (template -> opencode + pi derived files) ---
log "settings-sync..."
if ! uv run --directory "$CLAUDE_DIR/settings-sync" sync; then
  echo "error: settings-sync failed" >&2
  exit 1
fi

# --- 3. pi packages (declarative: install what's pinned but not yet on disk) ---
# The template pins packages[]; settings-sync wholesale-copied it to the pi
# agent settings.json above. Materialize any not yet fetched. The declaration
# can't itself be the "installed?" check (sync just made settings.json match the
# template, and `pi list` reads that declaration, not the filesystem), so probe
# the actual install location. PI_CODING_AGENT_DIR is unset above, so these
# resolve pi's default home (~/.pi/agent) regardless of launch shell.
#   npm:<name>[@version]   -> ~/.pi/agent/npm/node_modules/<name>
#   git:<host>/<path>       -> ~/.pi/agent/git/<host>/<path>
if command -v pi >/dev/null 2>&1; then
  tmpl="$CLAUDE_DIR/pi/settings.json"
  npm_root="$HOME/.pi/agent/npm/node_modules"
  git_root="$HOME/.pi/agent/git"
  if [ -f "$tmpl" ] && command -v jq >/dev/null 2>&1; then
    while IFS= read -r spec; do
      [ -z "$spec" ] && continue
      case "$spec" in
        npm:*)
          pkg="${spec#npm:}"
          if [[ "$pkg" == @* ]]; then
            scope="${pkg%%/*}"; rest="${pkg#*/}"; short="${rest%%@*}"; name="${scope}/${short}"
          else
            name="${pkg%%@*}"
          fi
          if [ -d "$npm_root/$name" ]; then
            log "pi: $name present, skipping"
          else
            log "pi install $spec"
            pi install "$spec" || warn "pi install $spec failed"
          fi
          ;;
        git:*)
          # git:<host>/<path> -> ~/.pi/agent/git/<host>/<path>
          gpath="${spec#git:}"
          if [ -d "$git_root/$gpath" ]; then
            log "pi: $gpath present, skipping"
          else
            log "pi install $spec"
            pi install "$spec" || warn "pi install $spec failed"
          fi
          ;;
        *)
          log "pi install $spec"
          pi install "$spec" || warn "pi install $spec failed"
          ;;
      esac
    done < <(jq -r '.packages[]? // empty' "$tmpl")
  elif ! command -v jq >/dev/null 2>&1; then
    warn "jq not found; cannot read packages[] from $tmpl — skipping pi packages"
  fi
else
  log "pi not on PATH; skipping pi packages"
fi

# --- 4. evo plugin for claude-code / opencode ---
# evo CLI is needed only for these two hosts (pi is handled above via pi install).
# Ensure the evo binary exists, then install the per-host plugin if missing.
needs_evo=0
command -v claude  >/dev/null 2>&1 && needs_evo=1
command -v opencode >/dev/null 2>&1 && needs_evo=1
if [ "$needs_evo" -eq 1 ]; then
  if ! command -v evo >/dev/null 2>&1; then
    log "installing evo CLI (evo-hq-cli)..."
    if ! uv tool install evo-hq-cli; then
      echo "error: uv tool install evo-hq-cli failed" >&2
      exit 1
    fi
  fi
  # claude-code: evo lives at ~/.claude/plugins/cache/<mkt>/evo/<version>/
  if command -v claude >/dev/null 2>&1; then
    if ls "$HOME/.claude/plugins/cache/"*/evo/*/ >/dev/null 2>&1; then
      log "evo: claude-code plugin present, skipping"
    else
      log "evo install claude-code..."
      evo install claude-code || warn "evo install claude-code failed"
    fi
  fi
  # opencode: evo lives at ~/.config/opencode/plugins/evo.js
  if command -v opencode >/dev/null 2>&1; then
    if [ -f "$HOME/.config/opencode/plugins/evo.js" ]; then
      log "evo: opencode plugin present, skipping"
    else
      log "evo install opencode..."
      evo install opencode || warn "evo install opencode failed"
    fi
  fi
else
  log "claude/opencode not on PATH; skipping evo host installs"
fi

# --- 5. vendored web-access extension deps ---
# The extension at pi/extensions/web-access/ is a vendored, stripped fork of
# pi-web-access v0.13.0. Its npm deps (readability, linkedom, p-limit, turndown,
# unpdf) install into a colocated node_modules/ that pi's extension loader resolves.
wa_dir="$CLAUDE_DIR/pi/extensions/web-access"
if [ -f "$wa_dir/package.json" ]; then
  if [ ! -d "$wa_dir/node_modules" ]; then
    log "npm install (web-access deps)..."
    (cd "$wa_dir" && npm install) || warn "npm install (web-access) failed"
  else
    log "web-access: node_modules present, skipping"
  fi
fi

exit "$exit_code"
