// bash-guard.js - opencode plugin (parity port of
// ~/.claude/custom/hooks/check-bash-guard.sh).
//
// Hard-denies S3 delete operations, all deletes under /mnt/data, and deletes
// on filesystem root, via the tool.execute.before plugin hook.
// Run with: node --test bash-guard.test.mjs
//
// Scope (mirrors the Claude hook):
//   S3:       deletes only blocked. Uploads (cp ./x s3://..., s3api put-*) and
//             read ops (ls, cp download, sync download, list-*/get-*) allowed.
//   /mnt/data: ALL deletes blocked (rm, rmdir, shred, unlink, trash,
//             find -delete, find -exec rm). Reads/writes allowed.
//
// Bypass-resistance mirrors the bash hook:
//   - S3 guard flattens shell separators + quote/subshell chars so wrapped
//     forms (bash -c "...", $(...), a && b) still match. Last-match-style scan
//     over a fixed 3-token sequence (aws s3 <sub>) prevents cross-boundary
//     leakage constructing a false match.
//   - /mnt/data guard splits on command separators FIRST, then within each
//     segment flattens only quote/subshell chars (NOT separators) and requires
//     /mnt/data to be an argument to the delete verb in the same segment. This
//     prevents false positives where the verb and /mnt/data appear as unrelated
//     words across a boundary (rm /tmp/x && echo cleaned /mnt/data done).
//
// Known limitation (accepted tradeoff, same as the bash hook): a delete verb
// nested in a quoted flag VALUE (git commit -m "rm ... /mnt/data ...") is
// indistinguishable from a quoted wrapper that EXECUTES (bash -c "rm ...").
// Both are denied; the user rewords if hit.

const S3_REASON =
  "S3 deletes are not permitted for the agent - run them yourself outside opencode. (plugin: bash-guard.js)"
const MNT_REASON =
  "Deletes under /mnt/data are not permitted for the agent - run them yourself outside opencode. (plugin: bash-guard.js)"
const ROOT_REASON =
  "Deletes on filesystem root are not permitted for the agent - run them yourself outside opencode. (plugin: bash-guard.js)"
const MNT_PARENT_REASON =
  "Deletes on /mnt (parent of /mnt/data) are not permitted for the agent - run them yourself outside opencode. (plugin: bash-guard.js)"
const SUDO_REASON =
  "sudo is not permitted for the agent - run it yourself outside opencode. (plugin: bash-guard.js)"
const DD_REASON =
  "dd is not permitted for the agent - destructive disk operations. (plugin: bash-guard.js)"
const MKFS_REASON =
  "mkfs is not permitted for the agent - destructive disk operations. (plugin: bash-guard.js)"
const CHMOD_REASON =
  "chmod 777 is not permitted for the agent - permission weakening. (plugin: bash-guard.js)"
const GIT_FORCE_REASON =
  "git push --force is not permitted for the agent - run it yourself outside opencode. (plugin: bash-guard.js)"
const GH_API_REASON =
  "gh api write methods are not permitted for the agent - run them yourself outside opencode. (plugin: bash-guard.js)"

// Cheap pre-check: skip unless something relevant is mentioned. Correctness
// does not depend on this (the guards return allow when nothing matches), it
// only keeps the common case fast.
const PRECHECK = /aws\s+s3(api)?\s|\/mnt\b|\b(rm|rmdir|shred|unlink|trash|find|sudo|dd|mkfs|chmod)\b|\bgit\s+(push|api)\b|\bgh\s+api\b/

// S3 guard: flatten separators + quote/subshell/backslash chars so wrapped/compound
// forms (bash -c "...", $(...), a && b, \rm) tokenize to bare tokens.
const S3_FLATTEN = /["'`$()|;&\\]/g
// Segment: flatten only quote/subshell/backslash chars (NOT separators, which
// were already split on).
const SEG_FLATTEN = /["'`$()\\]/g
const SPLIT_SEPS = /[\n;&|]/
const DELETE_VERBS = new Set(["rm", "rmdir", "shred", "unlink", "trash"])

// Collapse // -> / and /./ -> / so path-normalization bypasses (//mnt/data,
// /mnt/./data, //, /./) are caught. Does NOT resolve .. (the one .. case we
// tested, /mnt/data/.., is caught by the raw prefix match on /mnt/data).
function normalizePath(p) {
  return p.replace(/\/+/g, "/").replace(/\/\.\//g, "/").replace(/\/\.$/, "")
}

export function decide(command) {
  const allow = { deny: false }
  if (typeof command !== "string" || command === "") return allow
  if (!PRECHECK.test(command)) return allow

  // ---------- command-level guards (flattened tokens) ----------
  const tokens = command.replace(S3_FLATTEN, " ").split(/\s+/).filter(Boolean)
  const n = tokens.length

  // sudo: deny anywhere in the command (covers sudo rm, bash -c "sudo ...").
  if (tokens.includes("sudo")) {
    return { deny: true, reason: `Blocked: sudo is not permitted. ${SUDO_REASON}` }
  }

  // dd: deny anywhere (destructive disk operations).
  if (tokens.includes("dd")) {
    return { deny: true, reason: `Blocked: dd is not permitted. ${DD_REASON}` }
  }

  // mkfs: deny any token starting with mkfs (mkfs.ext4, mkfs.btrfs, ...).
  for (const t of tokens) {
    if (t.startsWith("mkfs")) {
      return { deny: true, reason: `Blocked: mkfs is not permitted. ${MKFS_REASON}` }
    }
  }

  // chmod 777: deny chmod with 777 as a subsequent arg (permission weakening).
  for (let i = 0; i < n; i++) {
    if (tokens[i] === "chmod") {
      for (let j = i + 1; j < n; j++) {
        if (tokens[j] === "777") {
          return { deny: true, reason: `Blocked: chmod 777 is not permitted. ${CHMOD_REASON}` }
        }
      }
    }
  }

  // git push --force/-f: deny force push (exact --force, not --force-with-lease).
  for (let i = 0; i + 2 < n; i++) {
    if (tokens[i] === "git" && tokens[i + 1] === "push") {
      for (let j = i + 2; j < n; j++) {
        if (tokens[j] === "--force" || tokens[j] === "-f") {
          return { deny: true, reason: `Blocked: git push --force is not permitted. ${GIT_FORCE_REASON}` }
        }
      }
    }
  }

  // gh api write methods: deny DELETE/POST/PATCH/PUT (via -X or --method[=])
  // or --input (sends a request body). GET is allowed. Catches wrapped forms
  // (bash -c, $(...)) via the flattened token scan.
  const GH_WRITE_METHODS = new Set(["DELETE", "POST", "PATCH", "PUT"])
  for (let i = 0; i + 1 < n; i++) {
    if (tokens[i] === "gh" && tokens[i + 1] === "api") {
      for (let j = i + 2; j < n; j++) {
        const t = tokens[j]
        if (t === "-X" || t === "--method") {
          const method = tokens[j + 1]
          if (method && GH_WRITE_METHODS.has(method)) {
            return { deny: true, reason: `Blocked: gh api -X ${method} is a write method. ${GH_API_REASON}` }
          }
        }
        if (t.startsWith("--method=")) {
          const method = t.slice(9)
          if (GH_WRITE_METHODS.has(method)) {
            return { deny: true, reason: `Blocked: gh api --method=${method} is a write method. ${GH_API_REASON}` }
          }
        }
        if (t === "--input") {
          return { deny: true, reason: `Blocked: gh api --input sends a request body. ${GH_API_REASON}` }
        }
      }
    }
  }

  // ---------- S3 guard ----------
  // When we find `aws`, skip flag tokens (--*) before looking for s3/s3api,
  // so `aws --profile=p s3 rm ...` is caught.
  for (let i = 0; i < n; i++) {
    if (tokens[i] === "aws") {
      let j = i + 1
      while (j < n && tokens[j].startsWith("-")) j++
      if (j >= n) continue
      if (tokens[j] === "s3") {
        const sub = tokens[j + 1]
        if (sub === "rm" || sub === "rb") {
          return { deny: true, reason: `Blocked: aws s3 ${sub} deletes S3 data. ${S3_REASON}` }
        }
        if (sub === "sync") {
          for (let k = j + 2; k < n; k++) {
            if (tokens[k] === "--delete") {
              return { deny: true, reason: `Blocked: aws s3 sync --delete removes S3 objects. ${S3_REASON}` }
            }
          }
        }
      }
      if (tokens[j] === "s3api") {
        const sub = tokens[j + 1]
        if (sub && sub.startsWith("delete-")) {
          return { deny: true, reason: `Blocked: aws s3api ${sub} deletes S3 data. ${S3_REASON}` }
        }
      }
    }
  }

  // ---------- segment-based path guards ----------
  for (const seg of command.split(SPLIT_SEPS)) {
    if (!seg.trim()) continue
    const s = seg.replace(SEG_FLATTEN, " ").split(/\s+/).filter(Boolean)
    const sn = s.length
    if (sn === 0) continue

    // rm|rmdir|shred|unlink|trash with a protected path among their args in
    // THIS segment. Flags are skipped so rearrangements (rm -rf, rm -r -f,
    // rm -fr) all match the same. Paths are normalized before matching so
    // //mnt/data, /mnt/./data, //, /./ are caught.
    for (let si = 0; si < sn; si++) {
      const verb = s[si]
      if (DELETE_VERBS.has(verb)) {
        for (let sj = si + 1; sj < sn; sj++) {
          const a = s[sj]
          if (a.startsWith("-")) continue
          const norm = normalizePath(a)
          if (norm.startsWith("/mnt/data")) {
            return { deny: true, reason: `Blocked: ${verb} on a path under /mnt/data. ${MNT_REASON}` }
          }
          if (norm === "/" || norm === "/*") {
            return { deny: true, reason: `Blocked: ${verb} on filesystem root. ${ROOT_REASON}` }
          }
          if (norm === "/mnt") {
            return { deny: true, reason: `Blocked: ${verb} on /mnt (parent of /mnt/data). ${MNT_PARENT_REASON}` }
          }
        }
      }
    }

    // find with a protected search path AND -delete/-exec rm/-ok rm in THIS segment.
    for (let si = 0; si < sn; si++) {
      if (s[si] !== "find") continue
      let searchPath = ""
      let sj = si + 1
      while (sj < sn) {
        const a = s[sj]
        if ((a.startsWith("-") && a.length >= 2) || a === "!" || a === "(" || a === ")") break
        if (!searchPath) searchPath = a
        sj++
      }
      const normPath = normalizePath(searchPath)
      if (normPath.startsWith("/mnt/data")) {
        for (let sk = si + 1; sk < sn; sk++) {
          if (s[sk] === "-delete" || s[sk] === "--delete") {
            return { deny: true, reason: `Blocked: find -delete on a path under /mnt/data. ${MNT_REASON}` }
          }
          if (s[sk] === "-exec" || s[sk] === "-execdir" || s[sk] === "-ok" || s[sk] === "-okdir") {
            for (let sm = sk + 1; sm < sn && sm < sk + 6; sm++) {
              if (s[sm] === "rm") {
                return { deny: true, reason: `Blocked: find ${s[sk]} rm on a path under /mnt/data. ${MNT_REASON}` }
              }
            }
          }
        }
      }
      break
    }
  }

  return allow
}

export const BashGuard = async () => ({
  "tool.execute.before": async (input, output) => {
    if (input?.tool !== "bash") return
    const command = output?.args?.command ?? ""
    if (!command) return
    const r = decide(command)
    if (r.deny) throw new Error(r.reason)
  },
})
