# CR8000-to-PS_Spec

A tool (a set of VS Code Copilot **Skills + Agents + Python scripts + MCP servers**) that builds a
**power distribution map** of an electronic product from **CR8000** CAD exports (ISCF + Partlist),
computes current consumption per power rail, and generates a **power distribution block diagram**.
Full specification (in Czech): [`Description.md`](Description.md).

## Goal
From two text exports out of CR8000 (ISCF + Testway Partlist):
1. deterministically match components to power rails,
2. decode rail voltages,
3. filter out negligible consumers,
4. fill operating voltages and currents from datasheets,
5. check consistency,
6. sum consumption per rail and roll currents up to the input rail (typically 24 V),
7. generate the `power_tree` (Mermaid / draw.io).

## Principles
1. **Source of truth:** user edits always take precedence over AI computation.
2. **No guessing:** non-deterministic results are never guessed — the system proposes a value
   plus methodology and requests user verification.
3. **Offline:** no internet search; only the supplied inputs and datasheets are used.

## Layout
- Shared (across projects): `python/`, `skills/`, `.github/`, `.vscode/`, `Data/components_data.md`.
- Schematic-version-specific data: `Data/<project>/<date>/` (e.g. `Data/MCP1x10/20260825/`).

## Language
Documentation and user-facing communication are in **Czech**; code and identifiers in **English**.
This README is the only English document (the project is currently single-user).

## Status
Specification in progress + scaffolding. Chosen `power_map` format: **HTML**.
Open items: see `Description.md`, section 15.
