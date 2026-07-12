#!/usr/bin/env bash
# PreToolUse hook: hard-deny S3 delete operations and all deletes under /mnt/data.
#
# Reads the Claude Code hook JSON from stdin; emits a deny decision JSON to
# stdout when the command would delete S3 data or delete anything under
# /mnt/data, otherwise emits nothing (allow).
#
# Bypass-resistance: no `if` matcher is used upstream (matchers fail open on
# $()/backticks). This script runs on every Bash command and uses a cheap
# grep pre-check, then tokenizes - flattening shell metachars
# (" ' ` $ ( ) ; & |) to spaces - so wrapped forms (bash -c "...", $(...),
# a && b, a ; b) still match. Layered with permissions.deny (unbypassable
# floor); this hook catches the wrapper/compound/flag-reorder cases the
# deny globs miss.
#
# Scope (per user choice):
#   S3:   hard deny deletes only. Uploads (aws s3 cp ./x s3://..., s3api put-*)
#         stay allowed. Read ops (ls, cp download, sync download, list-*/get-*)
#         stay allowed.
#   /mnt/data: deny ALL deletes under /mnt/data (rm, rmdir, shred, unlink, trash,
#         find ... -delete, find ... -exec rm). Reads/writes stay allowed.
#
# /mnt/data matching is structural, not co-occurrence: the command is split
# into subcommands on ; & | and newlines first, then within each segment the
# /mnt/data path must be an argument to the delete verb (or the search path
# of a `find ... -delete`). This prevents false positives where the verb and
# /mnt/data appear as unrelated words (e.g. inside a `git commit -m` message,
# or across an `&&` boundary: `rm /tmp/x && echo /mnt/data done`).
set -euo pipefail

cmd=$(jq -r '.tool_input.command // ""')
# Empty / missing command: nothing to enforce, stay silent.
[ -n "$cmd" ] || exit 0

deny() {
    local reason="$1"
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
    exit 0
}

# Cheap pre-check: skip unless something relevant is mentioned.
if ! echo "$cmd" | grep -qE 'aws[[:space:]]+s3(api)?[[:space:]]|/mnt/data|[[:space:]](rm|rmdir|shred|unlink|trash)([[:space:]]|$)|^find[[:space:]]'; then
    exit 0
fi

# Flatten shell quote / subshell / separator chars to spaces so wrapped forms
# (bash -c "aws s3 rm ...", $(aws s3 rm ...), a && aws s3 rm ...) tokenize into
# bare tokens. Used by the S3 guard, which matches a fixed 3-token sequence
# (aws s3 <sub>) so cross-boundary leakage can't construct a false match.
norm="${cmd//[\"\'\`\$\(\)\;\&\|]/ }"
# shellcheck disable=SC2206
tokens=($norm)
n=${#tokens[@]}

# ---------- S3 guard ----------
# aws s3 rm|rb           -> deny (destructive s3 subcommands)
# aws s3 sync --delete   -> deny (--delete removes dest files absent from source)
# aws s3api delete-*     -> deny (the delete-* family: delete-object(s),
#                                   delete-bucket(-*), delete-public-access-block, ...)
i=0
while (( i + 2 < n )); do
    if [[ "${tokens[i]}" == "aws" && "${tokens[i+1]}" == "s3" ]]; then
        sub="${tokens[i+2]}"
        case "$sub" in
            rm|rb)
                deny "Blocked: aws s3 ${sub} deletes S3 data. S3 deletes are not permitted for the agent - run them yourself outside Claude. (hook: check-delete-safety.sh)"
                ;;
            sync)
                # Look for --delete anywhere after `sync`. --delete makes sync
                # destructive (removes dest files absent from source).
                j=$((i + 3))
                while (( j < n )); do
                    if [[ "${tokens[j]}" == "--delete" ]]; then
                        deny "Blocked: aws s3 sync --delete removes S3 objects. S3 deletes are not permitted for the agent - run them yourself outside Claude. (hook: check-delete-safety.sh)"
                    fi
                    j=$((j + 1))
                done
                ;;
        esac
    fi
    if [[ "${tokens[i]}" == "aws" && "${tokens[i+1]}" == "s3api" ]]; then
        sub="${tokens[i+2]}"
        if [[ "$sub" == delete-* ]]; then
            deny "Blocked: aws s3api ${sub} deletes S3 data. S3 deletes are not permitted for the agent - run them yourself outside Claude. (hook: check-delete-safety.sh)"
        fi
    fi
    i=$((i + 1))
done

# ---------- /mnt/data guard ----------
# Split the command into subcommands on ; & | and newlines first, so a verb's
# args can't leak across a boundary. Within each segment, flatten only
# quote/subshell chars (NOT separators) and tokenize. The verb's args are
# then bounded to its own segment.
sep_re=$'[\n;&|]'
segs=()
while IFS= read -r seg || [ -n "$seg" ]; do
    [ -n "$seg" ] && segs+=("$seg")
done < <(printf '%s' "${cmd//$sep_re/$'\n'}")

for seg in "${segs[@]}"; do
    s_norm="${seg//[\"\'\`\$\(\)]/ }"
    # shellcheck disable=SC2206
    s=($s_norm)
    sn=${#s[@]}
    [ "$sn" -eq 0 ] && continue

    # rm|rmdir|shred|unlink|trash with a /mnt/data path among their args
    # in THIS segment.
    si=0
    while (( si < sn )); do
        st="${s[si]}"
        case "$st" in
            rm|rmdir|shred|unlink|trash)
                sj=$((si + 1))
                while (( sj < sn )); do
                    a="${s[sj]}"
                    if [[ "$a" != -?* && "$a" == /mnt/data* ]]; then
                        deny "Blocked: ${st} on a path under /mnt/data. Deletes under /mnt/data are not permitted for the agent - run them yourself outside Claude. (hook: check-delete-safety.sh)"
                    fi
                    sj=$((sj + 1))
                done
                ;;
        esac
        si=$((si + 1))
    done

    # find with a /mnt/data search path AND -delete or -exec rm in THIS segment.
    si=0
    while (( si < sn )); do
        if [[ "${s[si]}" == "find" ]]; then
            search_path=""
            sj=$((si + 1))
            while (( sj < sn )); do
                a="${s[sj]}"
                if [[ "$a" == -?* || "$a" == "!" || "$a" == "(" || "$a" == ")" ]]; then
                    break
                fi
                if [[ -z "$search_path" ]]; then
                    search_path="$a"
                fi
                sj=$((sj + 1))
            done
            if [[ "$search_path" == /mnt/data* ]]; then
                sk=$((si + 1))
                while (( sk < sn )); do
                    if [[ "${s[sk]}" == "-delete" || "${s[sk]}" == "--delete" ]]; then
                        deny "Blocked: find -delete on a path under /mnt/data. Deletes under /mnt/data are not permitted for the agent - run them yourself outside Claude. (hook: check-delete-safety.sh)"
                    fi
                    if [[ "${s[sk]}" == "-exec" || "${s[sk]}" == "-execdir" ]]; then
                        sm=$((sk + 1))
                        while (( sm < sn && sm < sk + 6 )); do
                            if [[ "${s[sm]}" == "rm" ]]; then
                                deny "Blocked: find -exec rm on a path under /mnt/data. Deletes under /mnt/data are not permitted for the agent - run them yourself outside Claude. (hook: check-delete-safety.sh)"
                            fi
                            sm=$((sm + 1))
                        done
                    fi
                    sk=$((sk + 1))
                done
            fi
            break
        fi
        si=$((si + 1))
    done
done

exit 0
