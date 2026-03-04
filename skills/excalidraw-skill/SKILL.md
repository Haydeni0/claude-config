---
name: excalidraw-skill
description: Programmatic canvas toolkit for creating, editing, and refining Excalidraw diagrams via MCP tools with real-time canvas sync. Use when an agent needs to (1) draw or lay out diagrams on a live canvas, (2) iteratively refine diagrams using describe_scene and get_canvas_screenshot to see its own work, (3) export/import .excalidraw files or PNG/SVG images, (4) save/restore canvas snapshots, (5) convert Mermaid to Excalidraw, or (6) perform element-level CRUD, alignment, distribution, grouping, duplication, and locking. Requires Docker and the MCP excalidraw canvas container running on port 3000.
---

# Excalidraw Skill

## Step 0: Verify MCP Connection

Before doing anything, confirm the MCP tools are available:

### Check 1: MCP tools registered

```bash
mcp-cli tools | grep excalidraw
```

If you see tools like `excalidraw/batch_create_elements` - proceed.

### Check 2: MCP tools not found - guide user to install

If MCP tools are not available, tell the user:
> The Excalidraw MCP server is not configured. To set up (requires Docker):
>
> 1. Start the canvas server:
>
>    ```
>    docker run -d -p 3000:3000 --name mcp-excalidraw-canvas ghcr.io/yctimlin/mcp_excalidraw-canvas:latest
>    ```
>
> 2. Open `http://localhost:3000` in a browser
> 3. Register the MCP server:
>
>    ```
>    claude mcp add excalidraw -s user -- docker run -i --rm \
>      -e EXPRESS_SERVER_URL=http://host.docker.internal:3000 \
>      -e ENABLE_CANVAS_SYNC=true \
>      ghcr.io/yctimlin/mcp_excalidraw:latest
>    ```
>
> 4. Restart your agent session so it picks up the new MCP server.

## Quality Gate (MANDATORY - read before creating any diagram)

**After EVERY iteration (each batch of elements added), you MUST run a quality check before proceeding. NEVER say "looks great" unless ALL checks pass.**

### Quality Checklist - verify ALL before adding more elements

1. **Text truncation**: Is ALL text fully visible? Labels must fit inside their shapes. If text is cut off or wrapping badly - increase `width` and/or `height`.
2. **Overlap**: Do ANY elements overlap each other? Check that no rectangles, ellipses, or text elements share the same space. Background zones must fully contain their children with padding.
3. **Arrow crossing**: Do arrows cross through unrelated elements or overlap with text labels? If yes - **use curved/elbowed arrows with waypoints** to route around obstacles (see "Arrow Routing" section). Never accept crossing arrows.
4. **Arrow-text overlap**: Do any arrow labels ("charge", "event", etc.) overlap with shapes? Arrow labels are positioned at the midpoint - if they overlap, either remove the label, shorten it, or adjust the arrow path.
5. **Spacing**: Is there at least 40px gap between elements? Cramped layouts are unreadable.
6. **Readability**: Can all labels be read at normal zoom? Font size >= 16 for body text, >= 20 for titles.

### If ANY issue is found

- **STOP adding new elements**
- Fix the issue first (resize, reposition, delete and recreate)
- Re-verify with a new screenshot
- Only proceed to next iteration after ALL checks pass

### Sizing Rules (prevent truncation)

- **Shape width**: `max(160, labelTextLength * 9)` pixels. For multi-word labels like "API Gateway (Kong)", count all characters.
- **Shape height**: 60px for single line, 80px for 2 lines, 100px for 3 lines.
- **Background zones**: Add 50px padding on ALL sides around contained elements.
- **Element spacing**: 60px vertical between tiers, 40px horizontal between siblings.
- **Side panels**: Place at least 80px away from main diagram elements.
- **Arrow labels**: Keep labels short (1-2 words). Long arrow labels overlap with other elements.

### Layout Planning (prevent overlap)

Before creating elements, **plan your coordinate grid** on paper first:

- Tier 1 (y=50-130): Client apps
- Tier 2 (y=200-280): Gateway/Edge
- Tier 3 (y=350-440): Services (spread wide: each service ~180px apart)
- Tier 4 (y=510-590): Data stores
- Side panels: x < 0 (left) or x > mainDiagramRight + 80 (right)

**Do NOT place side panels (observability, external APIs) at the same x-range as the main diagram - they WILL overlap.**

## Quick Start

1. Run **Step 0** above to verify MCP tools are available.
2. Open `http://localhost:3000` in a browser (required for image export/screenshot).
3. Use MCP tools for all operations.
4. For full tool reference, read `references/cheatsheet.md`.

## Workflow: Draw A Diagram

1. **Call `read_diagram_guide`** first to load design best practices.
2. **Plan your coordinate grid** (see Quality Gate - Layout Planning) before writing any JSON.
3. Optional: `clear_canvas` to start fresh.
4. Use `batch_create_elements` with shapes AND arrows in one call.
5. **Assign custom `id` to shapes** (e.g. `"id": "auth-svc"`). Set `text` field to label shapes.
6. **Size shapes for their text** - use `width: max(160, textLength * 9)`.
7. **Bind arrows** using `startElementId` / `endElementId` - arrows auto-route.
8. `set_viewport` with `scrollToContent: true` to auto-fit the diagram.
9. **Run Quality Checklist** - `get_canvas_screenshot` and critically evaluate. Fix issues before proceeding.

### Arrow Binding (Recommended)

Bind arrows to shapes for auto-routed edges using `startElementId` / `endElementId`:

```json
{"elements": [
  {"id": "svc-a", "type": "rectangle", "x": 0, "y": 0, "width": 120, "height": 60, "text": "Service A"},
  {"id": "svc-b", "type": "rectangle", "x": 0, "y": 200, "width": 120, "height": 60, "text": "Service B"},
  {"type": "arrow", "x": 0, "y": 0, "startElementId": "svc-a", "endElementId": "svc-b", "text": "calls"}
]}
```

Arrows without binding use manual `x`, `y`, `points` coordinates.

### Arrow Routing - Avoid Overlaps (Critical for complex diagrams)

Straight arrows (2-point) cause crossing and overlap in complex diagrams. **Use curved or elbowed arrows instead:**

**Option 1: Curved arrows** - add intermediate waypoints + `roundness`:

```json
{
  "type": "arrow", "x": 100, "y": 100,
  "points": [[0, 0], [50, -40], [200, 0]],
  "roundness": {"type": 2},
  "strokeColor": "#1971c2"
}
```

The waypoint `[50, -40]` pushes the arrow upward to arc over elements. `roundness: {type: 2}` makes it a smooth curve.

**Option 2: Elbowed arrows** - right-angle routing (L-shaped or Z-shaped):

```json
{
  "type": "arrow", "x": 100, "y": 100,
  "points": [[0, 0], [0, -50], [200, -50], [200, 0]],
  "elbowed": true,
  "strokeColor": "#1971c2"
}
```

**When to use which:**

- **Fan-out arrows** (one source - many targets): Use curved arrows with waypoints spread vertically to avoid overlapping each other.
- **Cross-lane arrows** (connecting to side panels): Use elbowed arrows that route around the main diagram - go UP first, then ACROSS, then DOWN.
- **Inter-service arrows** (horizontal connections): Use curved arrows with a slight vertical offset to avoid crossing through adjacent elements.

**Rule of thumb:** If an arrow would cross through an unrelated element, add a waypoint to route around it. Never accept crossing arrows - always fix them.

## Workflow: Iterative Refinement (Key Differentiator)

The feedback loop that makes this skill unique. **Each iteration MUST include a quality check.**

1. Add elements (`batch_create_elements`, `create_element`).
2. `set_viewport` with `scrollToContent: true`.
3. `get_canvas_screenshot` - **critically evaluate** against the Quality Checklist.
4. **If issues found** - fix them (`update_element`, `delete_element`, resize, reposition).
5. `get_canvas_screenshot` again - re-verify fix.
6. **Only proceed to next iteration when ALL quality checks pass.**

### How to critically evaluate a screenshot

- Look at EVERY label - is any text cut off or overflowing its container?
- Look at EVERY arrow - does any arrow pass through an unrelated element?
- Look at ALL element pairs - do any overlap or touch?
- Look at spacing - is anything crammed together?
- **Be honest.** If you see ANY issue, say "I see [issue], fixing it" - not "looks great".

Example flow:

```
batch_create_elements -> get_canvas_screenshot -> "text truncated on 2 shapes"
-> update_element (increase widths) -> get_canvas_screenshot -> "overlap between X and Y"
-> update_element (reposition) -> get_canvas_screenshot -> "all checks pass"
-> proceed to next iteration
```

## Workflow: Refine An Existing Diagram

1. `describe_scene` to understand current state.
2. Identify targets by id, type, or label text (not x/y coordinates).
3. `update_element` to move/resize/recolor, `delete_element` to remove.
4. `get_canvas_screenshot` to verify changes visually.
5. If updates fail: check element id exists (`get_element`), element isn't locked (`unlock_elements`).

## Workflow: File I/O (Diagrams-as-Code)

- Export to .excalidraw format: `export_scene` with optional `filePath`.
- Import from .excalidraw: `import_scene` with `mode: "replace"` or `"merge"`.
- Export to image: `export_to_image` with `format: "png"` or `"svg"` (requires browser open).

## Workflow: Snapshots (Save/Restore Canvas State)

1. `snapshot_scene` with a name before risky changes.
2. Make changes, `describe_scene` / `get_canvas_screenshot` to evaluate.
3. `restore_snapshot` to rollback if needed.

## Workflow: Duplication

- `duplicate_elements` with `elementIds` and optional `offsetX`/`offsetY` (default 20,20).
- Useful for creating repeated patterns or copying existing layouts.

## Points Format for Arrows/Lines

The `points` field accepts both formats:

- Tuple: `[[0, 0], [100, 50]]`
- Object: `[{"x": 0, "y": 0}, {"x": 100, "y": 50}]`

Both are normalized to tuples automatically.

## Workflow: Share Diagram (excalidraw.com URL)

1. Create your diagram using any of the above workflows.
2. `export_to_excalidraw_url` - uploads encrypted scene, returns a shareable URL.
3. Share the URL - anyone can open it in excalidraw.com to view and edit.

## Workflow: Viewport Control

- `set_viewport` with `scrollToContent: true` - auto-fit all elements (zoom-to-fit).
- `set_viewport` with `scrollToElementId: "my-element"` - center view on a specific element.
- `set_viewport` with `zoom: 1.5, offsetX: 100, offsetY: 200` - manual camera control.

## References

- `references/cheatsheet.md`: Complete MCP tool list (26 tools) + payload shapes.
