/**
 * Config Guard — pi port of the opencode config-guard hook.
 *
 * `~/.claude` is the single source of truth; the pi agent dir is the derived
 * target. This extension blocks the model from hand-editing anything under the
 * agent dir, so drift can't sneak in. Edit the source in `~/.claude` (or, for
 * glm-pi, the launcher), then re-sync / re-launch.
 *
 * The agent dir is resolved with getAgentDir(), which honors PI_CODING_AGENT_DIR
 * and falls back to ~/.pi/agent. This is the key detail: glm-pi points
 * PI_CODING_AGENT_DIR at /tmp/glm-pi-$USER, so a hardcoded ~/.pi/agent would
 * silently miss it and leave the glm-pi runtime config unguarded.
 *
 * Loaded directly from source by pi via the `extensions` pointer in the agent
 * dir's settings.json (itself a copy of ~/.claude/pi/settings.json). The
 * extension itself is never synced — pi reads it from source — so it covers
 * both plain `pi` and `glm-pi` from the one file at ~/.claude/pi/extensions/.
 *
 * Coverage:
 *  - write/edit tool calls targeting a path under the agent dir -> blocked
 *  - bash tool calls that write to / mutate a path under the agent dir -> blocked
 *    (redirection, tee, sed -i, dd of=, cp/install/rsync dest,
 *     mv/rm/rmdir/shred/unlink operands). Closes the echo>file loophole.
 *
 * Not a shell parser — a conservative heuristic. False positives only bite when
 * a detected token resolves under the agent dir, which for a non-write command
 * is effectively never (reads like cat, ls, grep, diff, wc, stat carry no write
 * operator and aren't dispatched as mutating commands). Reads of the agent dir
 * via bash remain allowed.
 *
 * Safety: this only intercepts the MODEL's tool_call events. pi's own internal
 * writes (auth.json, lastChangelogVersion, sessions/) don't fire tool_call, so
 * blocking the model from the whole agent dir can't break them.
 *
 * Parity vs the opencode hook (~/.claude/opencode/plugins/config-guard.js):
 *  - opencode blocks edit/write/apply_patch + bash writes under ~/.config/opencode
 *    (or $OPENCODE_CONFIG_DIR). This file is the pi equivalent.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { getAgentDir } from "@earendil-works/pi-coding-agent";
import path from "node:path";
import os from "node:os";

function expandHome(p: string, home: string): string {
  return p
    .replace(/^~/, home)
    .replace(/\$HOME/g, home)
    .replace(/\$\{HOME\}/g, home);
}

// Strip one layer of surrounding quotes. Compare by char code to avoid fragile
// nested quote literals (a hand-written quote-in-quotes pair is error-prone
// and was the source of an unterminated-string bug here).
function stripQuotes(s: string): string {
  if (s.length >= 2) {
    const a = s.charCodeAt(0);
    const b = s.charCodeAt(s.length - 1);
    // 34 = double quote, 39 = single quote
    if ((a === 34 && b === 34) || (a === 39 && b === 39)) return s.slice(1, -1);
  }
  return s;
}

// First command word of a segment, skipping a leading `sudo` and any
// `FOO=bar` env assignments, so `sudo rm x` / `FOO=1 tee x` dispatch correctly.
function firstCommandWord(seg: string): string {
  const s = seg.trim().replace(/^sudo\s+/, "").replace(/^(?:[A-Za-z_]\w*=\S+\s+)+/, "");
  const m = s.match(/^([A-Za-z_][\w-]*)/);
  return m ? m[1] : "";
}

// Returns the first path the command writes to / mutates under `dir`, else null.
// Splits on shell sequencing operators so each stage of a chain is checked.
function bashWriteTarget(command: string, dir: string, home: string): string | null {
  const sep = path.sep;
  const resolve = (p: string): string => path.resolve(expandHome(stripQuotes(p), home));
  const under = (p: string): boolean => {
    const r = resolve(p);
    return r === dir || r.startsWith(dir + sep);
  };
  const targetOf = (p: string): string | null => (under(p) ? resolve(p) : null);

  // file-targeting redirection: append/overwrite, fd-prefixed, both-streams, noclobber
  const redir = /(?:[12]>>?|&>>|&>|>>|>\||>)/g;

  // Split on sequencing operators, but NOT on the | in >| (noclobber) or |&
  // (csh both-streams pipe) — those | are part of a redirect/pipe operator, not
  // a statement separator. Lookbehind/lookahead guard the bare-pipe alternative.
  for (const seg of command.split(/&&|\|\||;|(?<!>)\|(?![&|])/)) {
    // 1) redirection to a file (works for any command, incl. heredoc cat>f <<E)
    redir.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = redir.exec(seg)) !== null) {
      const rest = seg.slice(m.index + m[0].length);
      const tok = rest.match(/^\s*(\S+)/);
      if (tok) {
        const t = targetOf(tok[1]);
        if (t) return t;
      }
    }

    const cmd = firstCommandWord(seg);
    const toks = seg.trim().split(/\s+/).slice(1).filter((t) => t && !t.startsWith("-"));

    // 2) tee writes to its path operands
    if (cmd === "tee") {
      for (const t of toks) {
        const r = targetOf(t);
        if (r) return r;
      }
    }

    // 3) sed in-place edits its file operands (without -i it only reads)
    if (cmd === "sed" && /(^|\s)-i\b|(^|\s)--in-place\b/.test(seg)) {
      for (const t of toks) {
        const r = targetOf(t);
        if (r) return r;
      }
    }

    // 4) dd of=PATH
    if (cmd === "dd") {
      const dd = /\bof=(\S+)/g;
      while ((m = dd.exec(seg)) !== null) {
        const r = targetOf(m[1]);
        if (r) return r;
      }
    }

    // 5) cp/install/rsync: only the destination (last operand) is mutated
    if (cmd === "cp" || cmd === "install" || cmd === "rsync") {
      if (toks.length) {
        const r = targetOf(toks[toks.length - 1]);
        if (r) return r;
      }
    }

    // 6) mv: any operand is mutated (covers move-out and move-in)
    //    rm/rmdir/shred/unlink: any operand is deleted
    if (cmd === "mv" || cmd === "rm" || cmd === "rmdir" || cmd === "shred" || cmd === "unlink") {
      for (const t of toks) {
        const r = targetOf(t);
        if (r) return r;
      }
    }
  }
  return null;
}

export default function (pi: ExtensionAPI) {
  // Resolve the agent dir the way pi itself does: honors PI_CODING_AGENT_DIR,
  // falling back to ~/.pi/agent. Read at handler time, not module load, so a
  // changed env between sessions is picked up (and the value is always live).
  const DERIVED_DIR = getAgentDir();
  const prefix = DERIVED_DIR + path.sep;
  const home = os.homedir();

  const fileTools = new Set(["write", "edit"]);

  const reason = (tool: string, target: string, via: string): string =>
    `BLOCKED: ${target} is a derived target under the pi agent dir ` +
    `(${DERIVED_DIR}), reached via ${tool}${via}. For the default agent dir it ` +
    `is synced from ~/.claude/ via settings-sync; for a PI_CODING_AGENT_DIR ` +
    `override (e.g. glm-pi /tmp/glm-pi-$USER) it is regenerated by the launcher. ` +
    `Edit the ~/.claude/ source (or the launcher), not this file. ` +
    `See ~/.claude/pi/README.md.`;

  pi.on("tool_call", async (event, ctx) => {
    // 1) write/edit -> path arg
    if (fileTools.has(event.toolName)) {
      const raw = (event.input as { path?: string } | undefined)?.path;
      if (!raw) return undefined;
      const resolved = path.resolve(raw.replace(/^~/, home));
      if (resolved === DERIVED_DIR || resolved.startsWith(prefix)) {
        if (ctx.hasUI) {
          ctx.ui.notify(`Blocked ${event.toolName} to derived path: ${resolved}`, "warning");
        }
        return { block: true, reason: reason(event.toolName, resolved, "") };
      }
      return undefined;
    }

    // 2) bash -> scan for a write/mutate target under the agent dir
    if (event.toolName === "bash") {
      const command = (event.input as { command?: string } | undefined)?.command;
      if (!command) return undefined;
      const target = bashWriteTarget(command, DERIVED_DIR, home);
      if (target) {
        if (ctx.hasUI) {
          ctx.ui.notify(`Blocked bash write to derived path: ${target}`, "warning");
        }
        const snippet = command.length > 120 ? command.slice(0, 117) + "..." : command;
        return { block: true, reason: reason("bash", target, ` (command: ${snippet})`) };
      }
    }

    return undefined;
  });
}
