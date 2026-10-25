# Command interface

`inventor_schema` returns the authoritative JSON Schema and configured workspace. `inventor_validate` checks the schema, measurement policy, source paths and output collisions without COM. `inventor_status` reads the running release. `inventor_execute` performs the command and returns a structured report.

All tools use the fixed installation workspace. There is no agent-controlled arbitrary workspace override in MCP. The CLI allows `--workspace` for explicit local usage. Paths must resolve inside it. No output overwrite, shell command or Python expression API is exposed.

Commands use `schema_version: "1.0"`, a unique `request_id`, `units: "mm"`, `action`, `operations` and a new `output` filename. Actions: `create_part`, `create_assembly`, `modify`, `inspect`. Modify/inspect require `input`; inspect requires no operations and cannot export or finish geometry.

Each operation has `id`, `type` and `depends_on`. References name prior operations; for persisted references in a modify command prefix `@`. Built-in origin planes/axes need no dependency. Parameter expressions accept a parameter identifier, not arbitrary formulas or code. See the JSON examples and returned schema for exact fields.

Run `bracket.json` first to create the input used by `assembly.json`, `modify.json` and `inspect.json`. The `image_interpretation.json` file is an intentionally incomplete intake template: it must fail execution until measurements and geometry are supplied. It is not a runnable image-to-CAD demonstration.

## Monolithic and appearance example

Use [colored_block.json](../examples/colored_block.json). It creates a 40 × 30 × 10 mm box, consolidates the B-Rep into one base feature and colors one face blue.

- `monolithic: true` is allowed only for `create_part`. Exactly one solid is required. Construction sketches/features and their references are not kept in the final document. The report preserves the rebuild command.
- `expected_size_mm: [x,y,z]` checks the final axis-aligned envelope within 0.01 mm.
- `appearances.palette`: named `rgb: [0..255,0..255,0..255]`, optional `gloss: 0..1`, `metallic: true/false`.
- `appearances.base`: document appearance name.
- `appearances.regions`: named appearance and `box_mm: {min:[x,y,z],max:[x,y,z]}`. Each face is selected by a representative `PointOnFace`; this does not clip faces and is not a centroid guarantee. Last matching region wins. `min_faces` defaults to 1; set `max_faces` to catch accidental matches.

Appearances are applied after consolidation and do not alter physical material/density. Applying new appearances to a modified part can conflict with existing `AI_` asset names; use new palette names. Geometry-free sketch-only parts are supported without monolithic/envelope options.

## Failures and verification

The runner checks feature health and volume changes after operations. Modeling failures abort the active transaction and close only bridge-owned documents without saving. Saving and exporting are separate stages: a failed export can leave a valid native output and earlier exports. Check `success`, `native_saved`, `error`, `rolled_back` and `warnings`; never assume total filesystem rollback.

Snapshots activate the bridge document and adjust its camera. Existing user documents are not modified; the active view may change. A successful native file has a neighboring `.ipt.bridge.json` or `.iam.bridge.json` report with version, operations and source hashes. It can contain local paths and submitted measurements; review before sharing.
