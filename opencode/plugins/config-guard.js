import path from "path"
import os from "os"

const CONFIG_DIR = path.join(os.homedir(), ".config", "opencode")

export const ConfigGuard = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      const blockingTools = ["edit", "write", "apply_patch"]
      if (!blockingTools.includes(input.tool)) return

      const filePath = output.args.filePath || output.args.path || ""
      if (!filePath) return

      const resolved = path.resolve(filePath)
      if (resolved.startsWith(CONFIG_DIR + path.sep)) {
        throw new Error(
          `BLOCKED: ${resolved} is a derived target synced from ~/.claude/. ` +
          `Edit the ~/.claude/ source instead, then run ` +
          `sync opencode <step> --force. ` +
          `See AGENTS.md config management rules.`
        )
      }
    },
  }
}
