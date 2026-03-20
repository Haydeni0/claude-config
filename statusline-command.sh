#!/usr/bin/env bash

# --- Hook mode: track skill usage ---
# Called with --hook for PreToolUse and UserPromptSubmit events
if [ "$1" = "--hook" ]; then
    hook_input=$(cat)
    session_id=$(echo "$hook_input" | jq -r '.session_id // ""')
    hook_event=$(echo "$hook_input" | jq -r '.hook_event_name // ""')
    tool_name=$(echo "$hook_input" | jq -r '.tool_name // ""')
    skill=""

    if [ "$hook_event" = "PreToolUse" ] && [ "$tool_name" = "Skill" ]; then
        skill=$(echo "$hook_input" | jq -r '.tool_input.skill // ""')
    elif [ "$hook_event" = "UserPromptSubmit" ]; then
        prompt=$(echo "$hook_input" | jq -r '.prompt // ""')
        skill=$(echo "$prompt" | grep -oE '^/[a-zA-Z0-9_:-]+' | sed 's|^/||')
    fi

    if [ -n "$skill" ] && [ -n "$session_id" ]; then
        log_file="$HOME/.claude/statusline-skills-${session_id}.log"
        echo "$(date +%s)|${session_id}|${skill}|${hook_event}" >> "$log_file"
    fi
    echo "{}"
    exit 0
fi

input=$(cat)

# --- Parse JSON fields ---
model_name=$(echo "$input" | jq -r '.model.display_name // .model // "?"')
cwd=$(echo "$input" | jq -r '.cwd // .workspace.current_dir // "~"')
cost_usd=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
duration_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
total_in=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
cur_in=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
cache_create=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
context_size=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')
session_id=$(echo "$input" | jq -r '.session_id // ""')

# --- Colors (ANSI 256) ---
cyn=$'\033[36m'
mag=$'\033[35m'
slt=$'\033[38;2;94;115;168m'   # #5e73a8 slate blue
cfb=$'\033[38;2;100;149;237m'  # cornflower blue #6495ed
blu=$'\033[34m'
grn=$'\033[32m'
ylw=$'\033[33m'
red=$'\033[31m'
dim=$'\033[90m'   # brightBlack
rst=$'\033[0m'
sep=" | "

# ============================================================
# Widget: model  (cyan)
# ============================================================
model_w="${cyn}Model: ${model_name}${rst}"

# ============================================================
# Widget: context-bar  (brightBlack, 16-char bar / progress-short)
# ============================================================
used_tokens=$((cur_in + cache_create + cache_read))
[ "$context_size" -le 0 ] 2>/dev/null && context_size=200000

used_pct_raw=$(echo "scale=4; $used_tokens * 100 / $context_size" | bc -l 2>/dev/null || echo "0")
used_pct=$(printf "%.0f" "$used_pct_raw" 2>/dev/null || echo "0")
filled=$(printf "%.0f" "$(echo "$used_pct * 16 / 100" | bc -l 2>/dev/null || echo 0)")
[ "$filled" -gt 16 ] 2>/dev/null && filled=16

bar=""
for ((i=0; i<16; i++)); do
    if [ "$i" -lt "$filled" ] 2>/dev/null; then
        if   [ "$used_pct" -lt 50 ] 2>/dev/null; then bar+="${grn}█"
        elif [ "$used_pct" -lt 75 ] 2>/dev/null; then bar+="${ylw}█"
        else bar+="${red}█"; fi
    else
        bar+="${dim}░"
    fi
done
bar+="${rst}"

usedK=$((used_tokens / 1000))
totalK=$((context_size / 1000))
ctx_w="${dim}Context: ${bar}${dim} ${usedK}k/${totalK}k (${used_pct}%)${rst}"

# ============================================================
# Widget: session-cost  (magenta)
# ============================================================
cost_fmt=$(printf '$%.2f' "$cost_usd")
cost_w="${slt}Cost: ${cost_fmt}${rst}"

# ============================================================
# Widget: skills  (magenta, mode=current)
# ============================================================
skills_w="${dim}Skill: none${rst}"
if [ -n "$session_id" ]; then
    skill_log="$HOME/.claude/statusline-skills-${session_id}.log"
    if [ -f "$skill_log" ]; then
        last_skill=$(tail -1 "$skill_log" | cut -d'|' -f3)
        [ -n "$last_skill" ] && skills_w="${mag}Skill: ${last_skill}${rst}"
    fi
fi

# ============================================================
# Widget: thinking-effort  (magenta)
# ============================================================
effort=$(jq -r '.effortLevel // "medium"' "$HOME/.claude/settings.json" 2>/dev/null || echo "medium")
thinking_w="${slt}Thinking: ${effort}${rst}"

# ============================================================
# Widget: input-speed  (cyan) - session average
# ============================================================
speed_w=""
total_secs=$((duration_ms / 1000))
if [ "$total_secs" -gt 0 ] && [ "$total_in" -gt 0 ] 2>/dev/null; then
    in_speed_raw=$(echo "scale=2; $total_in / $total_secs" | bc -l 2>/dev/null || echo "0")
    if [ "$(echo "$in_speed_raw >= 1000" | bc -l 2>/dev/null)" = "1" ]; then
        fmt=$(echo "scale=1; $in_speed_raw / 1000" | bc -l 2>/dev/null)
        speed_w="${cyn}In: ${fmt}k/s${rst}"
    else
        fmt=$(printf "%.1f" "$in_speed_raw" 2>/dev/null || echo "$in_speed_raw")
        speed_w="${cyn}In: ${fmt}/s${rst}"
    fi
fi

# ============================================================
# Widget: git-root-dir  (cyan)
# ============================================================
cd "$cwd" 2>/dev/null || cd ~
git_root_w=""
if git rev-parse --git-dir >/dev/null 2>&1; then
    root_dir=$(git rev-parse --show-toplevel 2>/dev/null)
    if [ -n "$root_dir" ]; then
        root_name="${root_dir##*/}"
        git_root_w="${cyn}${root_name}${rst}"
    fi
fi
[ -z "$git_root_w" ] && git_root_w="${dim}no git${rst}"

# ============================================================
# Widget: git-branch  (magenta)
# ============================================================
git_branch_w=""
if git rev-parse --git-dir >/dev/null 2>&1; then
    branch=$(git branch --show-current 2>/dev/null)
    if [ -n "$branch" ]; then
        git_branch_w="${slt}⎇ ${branch}${rst}"
    fi
fi
[ -z "$git_branch_w" ] && git_branch_w="${slt}⎇ no git${rst}"

# ============================================================
# Widget: current-working-dir  (blue)
# ============================================================
display_cwd="${cwd/#$HOME/~}"
cwd_w="${cfb}${display_cwd}${rst}"

# ============================================================
# Output
# ============================================================

# Line 1: model | ctx | cost | skills | thinking | speed
line1="${model_w}${sep}${ctx_w}${sep}${cost_w}${sep}${skills_w}${sep}${thinking_w}"
[ -n "$speed_w" ] && line1+="${sep}${speed_w}"

# Line 2: git-root-dir | git-branch | cwd
line2="${git_root_w}${sep}${git_branch_w}${sep}${cwd_w}"

printf '%s\n' "$line1"
printf '%s'   "$line2"
