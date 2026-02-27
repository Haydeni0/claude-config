#!/usr/bin/env bash

input=$(cat)

# --- Extract fields (correct paths from official docs) ---
model_name=$(echo "$input" | jq -r '.model.display_name // "?"')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // "~"')
project_dir=$(echo "$input" | jq -r '.workspace.project_dir // ""')
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // 100')
total_in=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_out=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')
cur_in=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // 0')
cur_out=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // 0')
cache_create=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')
context_size=$(echo "$input" | jq -r '.context_window.context_window_size // 200000')
cost_usd=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
duration_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
api_ms=$(echo "$input" | jq -r '.cost.total_api_duration_ms // 0')
lines_added=$(echo "$input" | jq -r '.cost.total_lines_added // 0')
lines_removed=$(echo "$input" | jq -r '.cost.total_lines_removed // 0')
version=$(echo "$input" | jq -r '.version // ""')
session_id=$(echo "$input" | jq -r '.session_id // ""')

# --- Colors ---
red=$'\033[31m'; grn=$'\033[32m'; ylw=$'\033[33m'; blu=$'\033[34m'
mag=$'\033[35m'; cyn=$'\033[36m'; dim=$'\033[90m'; bld=$'\033[1m'; rst=$'\033[0m'; wht=$'\033[97m'
# Powerline separator
sep=" ${dim}${rst} "

# --- Format tokens ---
fmt() {
    local n=$1
    if [ "$n" -ge 1000000 ] 2>/dev/null; then echo "$(echo "scale=1; $n/1000000" | bc -l)M"
    elif [ "$n" -ge 1000 ] 2>/dev/null; then echo "$(echo "scale=1; $n/1000" | bc -l)K"
    else echo "$n"; fi
}

# --- [89] Gradient progress bar (20 chars) ---
filled=$(printf "%.0f" "$(echo "$used_pct * 0.2" | bc -l 2>/dev/null || echo 0)")
bar=""
for ((i=0; i<filled && i<20; i++)); do
    if [ $i -lt 7 ]; then bar+=$'\033[32m'"█"  # green
    elif [ $i -lt 14 ]; then bar+=$'\033[33m'"█" # yellow
    else bar+=$'\033[31m'"█"; fi                  # red
done
for ((i=filled; i<20; i++)); do bar+="${dim}░"; done
bar+="${rst}"

# --- Cost ---
if [ "$(echo "$cost_usd < 0.01" | bc -l 2>/dev/null)" = "1" ]; then cost_str='<$0.01'
elif [ "$(echo "$cost_usd < 1" | bc -l 2>/dev/null)" = "1" ]; then cost_str=$(printf '$%.3f' "$cost_usd")
else cost_str=$(printf '$%.2f' "$cost_usd"); fi

# --- Duration ---
total_secs=$((duration_ms / 1000))
api_secs=$((api_ms / 1000))
h=$((total_secs / 3600)); m=$(((total_secs % 3600) / 60)); s=$((total_secs % 60))
if [ $h -gt 0 ]; then dur="${h}h${m}m"
elif [ $m -gt 0 ]; then dur="${m}m${s}s"
else dur="${s}s"; fi


# --- Burn rate & ETA ---
burn_str=""
if [ $total_secs -gt 0 ]; then
    tpm=$(echo "scale=0; ($total_in + $total_out) * 60 / $total_secs" | bc -l 2>/dev/null || echo "0")
    if [ "$tpm" -gt 0 ] 2>/dev/null; then
        used_tokens=$((cur_in + cache_create + cache_read))
        remaining=$((context_size - used_tokens))
        if [ "$remaining" -gt 0 ] 2>/dev/null; then
            ml=$(echo "scale=0; $remaining / $tpm" | bc -l 2>/dev/null || echo "?")
            if [ "$ml" -lt 60 ] 2>/dev/null; then eta="~${ml}m"
            else eta="~$((ml / 60))h"; fi
        else
            eta="full!"
        fi
        burn_str="${tpm}t/m ${eta}"
    fi
fi

# --- Cost per minute ---
cpm_str=""
if [ $total_secs -gt 60 ]; then
    cpm=$(echo "scale=3; $cost_usd * 60 / $total_secs" | bc -l 2>/dev/null || echo "0")
    cpm_str="$(printf '$%.2f/m' "$cpm")"
fi

# --- Cache hit rate ---
cache_str=""
total_cache=$((cache_create + cache_read))
if [ "$total_cache" -gt 0 ] 2>/dev/null; then
    hit_pct=$(echo "scale=0; $cache_read * 100 / ($cache_read + $cache_create + $cur_in)" | bc -l 2>/dev/null || echo "0")
    cache_str="${hit_pct}%"
fi

# --- Lines changed ---
lines_str=""
if [ "$lines_added" -gt 0 ] 2>/dev/null || [ "$lines_removed" -gt 0 ] 2>/dev/null; then
    lines_str="${grn}+${lines_added}${rst}/${red}-${lines_removed}${rst}"
fi

# --- Git (with caching for perf) ---
CACHE_FILE="/tmp/claude-statusline-git-cache"
CACHE_MAX_AGE=5
cd "$cwd" 2>/dev/null || cd ~

cache_stale() {
    [ ! -f "$CACHE_FILE" ] || \
    [ $(($(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0))) -gt $CACHE_MAX_AGE ]
}

if cache_stale; then
    if git rev-parse --git-dir > /dev/null 2>&1; then
        branch=$(git branch --show-current 2>/dev/null || echo "detached")
        staged=$(git diff --cached --numstat 2>/dev/null | wc -l | tr -d ' ')
        unstaged=$(git diff --numstat 2>/dev/null | wc -l | tr -d ' ')
        untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
        echo "${branch}|${staged}|${unstaged}|${untracked}" > "$CACHE_FILE"
    else
        echo "|||" > "$CACHE_FILE"
    fi
fi

IFS='|' read -r branch staged unstaged untracked < "$CACHE_FILE"

git_str=""
if [ -n "$branch" ]; then
    dirty=""
    [ "$staged" -gt 0 ] 2>/dev/null && dirty+=" ${grn}S:${staged}${rst}"
    [ "$unstaged" -gt 0 ] 2>/dev/null && dirty+=" ${ylw}U:${unstaged}${rst}"
    [ "$untracked" -gt 0 ] 2>/dev/null && dirty+=" ${red}A:${untracked}${rst}"
    if [ -n "$dirty" ]; then
        git_str="${ylw}${branch}${rst}${dirty}"
    else
        git_str="${grn}${branch}${rst}"
    fi
fi

# --- [25/26/27] Daily/Weekly/Monthly cumulative cost (cached, 30s refresh) ---
COST_LOG="$HOME/.claude/statusline-cost-log"
COST_CACHE="/tmp/claude-statusline-cost-totals"
COST_CACHE_AGE=30

# Append current session cost to log
today=$(date +%Y-%m-%d)
echo "${today}|${session_id}|${cost_usd}" >> "$COST_LOG" 2>/dev/null

cost_totals_stale() {
    [ ! -f "$COST_CACHE" ] || \
    [ $(($(date +%s) - $(stat -f %m "$COST_CACHE" 2>/dev/null || stat -c %Y "$COST_CACHE" 2>/dev/null || echo 0))) -gt $COST_CACHE_AGE ]
}

daily_cost=""
if cost_totals_stale && [ -f "$COST_LOG" ]; then
    # Deduplicate: keep latest cost per session_id per day, then sum
    d_cost=$(awk -F'|' -v d="$today" '$1==d {a[$2]=$3} END {s=0; for(k in a) s+=a[k]; printf "%.2f",s}' "$COST_LOG" 2>/dev/null || echo "0")
    echo "${d_cost}" > "$COST_CACHE"
fi

if [ -f "$COST_CACHE" ]; then
    read -r daily_cost < "$COST_CACHE"
fi

cost_history_str=""
if [ -n "$daily_cost" ] && [ "$daily_cost" != "0.00" ] 2>/dev/null; then
    cost_history_str="today:\$${daily_cost}"
fi


# --- MCP server count (from enabled plugins + mcpServers) ---
mcp_str=""
mcp_count=0
if [ -f "$HOME/.claude/settings.json" ]; then
    # Count enabledPlugins (these provide MCP servers)
    plugin_count=$(jq '[.enabledPlugins // {} | to_entries[] | select(.value == true)] | length' "$HOME/.claude/settings.json" 2>/dev/null || echo "0")
    # Count mcpServers if any
    server_count=$(jq '.mcpServers // {} | keys | length' "$HOME/.claude/settings.json" 2>/dev/null || echo "0")
    mcp_count=$((plugin_count + server_count))
fi
[ "$mcp_count" -gt 0 ] 2>/dev/null && mcp_str="${mcp_count}"

# --- [97/98] Productivity score & rank ---
prod_str=""
rank_str=""
if [ "$(echo "$cost_usd > 0.01" | bc -l 2>/dev/null)" = "1" ]; then
    # Productivity = output tokens per dollar
    prod=$(echo "scale=0; $total_out / $cost_usd" | bc -l 2>/dev/null || echo "0")
    prod_str="${prod}tok/\$"

    # Rank based on output tokens per dollar
    if [ "$prod" -ge 50000 ] 2>/dev/null; then rank_str="🏆"
    elif [ "$prod" -ge 20000 ] 2>/dev/null; then rank_str="🥇"
    elif [ "$prod" -ge 10000 ] 2>/dev/null; then rank_str="🥈"
    elif [ "$prod" -ge 5000 ] 2>/dev/null; then rank_str="🥉"
    else rank_str=""; fi
fi

# --- Folder name ---
dir_name="${cwd##*/}"

# --- [87] Emoji mode + [85] Powerline arrows --- Build output ---
parts=""
parts+="📁 ${wht}${dir_name}${rst}"
parts+="${sep}${cyn}🤖 ${model_name}${rst}"
parts+="${sep}${bar} $(printf '%.0f' "$used_pct")%"
parts+="${sep}↑$(fmt $total_in) ↓$(fmt $total_out)"
parts+="${sep}💰 ${bld}${cost_str}${rst}"
[ -n "$cpm_str" ] && parts+=" ${dim}${cpm_str}${rst}"
[ -n "$cost_history_str" ] && parts+="${sep}📊 ${dim}${cost_history_str}${rst}"
[ -n "$burn_str" ] && parts+="${sep}🔥 ${dim}${burn_str}${rst}"
[ -n "$lines_str" ] && parts+="${sep}✏️  ${lines_str}"
[ -n "$cache_str" ] && parts+="${sep}💾 ${dim}${cache_str}${rst}"
[ -n "$prod_str" ] && parts+="${sep}⚡ ${dim}${prod_str}${rst}"
[ -n "$rank_str" ] && parts+=" ${rank_str}"
[ -n "$git_str" ] && parts+="${sep}🌿 ${git_str}"
parts+="${sep}🕐 ${dim}$(date '+%H:%M')${rst}"
# Remaining time (from burn rate ETA)
if [ -n "$eta" ]; then
    parts+="${sep}⏳ ${dim}${eta}${rst}"
fi

echo "$parts"
