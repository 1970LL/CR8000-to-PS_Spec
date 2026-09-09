"""Staging + per-component SpecPack build/index z potvrzeného párování (bez LLM).

Pipeline (deterministická, bez jazykového modelu):
1. Načte klíče komponent z Partlistu (``A5E__SLUG(COMMENT)``) přes parse_partlist.
2. Načte **confirmed** páry z ``datasheet_pairing.md`` (a5e -> datasheet(y)).
3. Vytvoří staging adresář s **HARDLINKY** na potvrzená PDF (bez kopií). Osiřelá /
   future PDF se nestagují, takže se nestaví.
4. Vygeneruje SpecPack config s ``workspaces:`` sekcí: ``ws_name`` = klíč komponenty,
   ``match`` = jména PDF. Multi-doc komponenta = víc match vzorů -> jeden workspace.
5. Spustí ``specpack build --workspaces`` + ``specpack index --workspaces`` do sdíleného
   rootu. Tím se opouští ``--per-doc`` (per-datasheet) ve prospěch per-komponenty.

Použití:
    python build_datasheet_workspaces.py                 # incremental build + index
    python build_datasheet_workspaces.py --full          # plný rebuild
    python build_datasheet_workspaces.py --no-build       # jen staging + config

Viz python/build_component_catalog.py, datasheet_pairing.md a python/README.md.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_specpack_index import (  # noqa: E402
    DEFAULT_COMPONENTS,
    DEFAULT_CONFIG,
    DEFAULT_ROOT,
    resolve_specpack,
    run,
)
from parse_partlist import aggregate_components, parse_partlist  # noqa: E402

_PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_PARTLIST = _PROJECT / "Data" / "MCP1x10" / "20260825" / "Partlist_Test.txt"
DEFAULT_STAGING = Path(r"D:\Code\Tools\specPack\staging")


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def parse_pairing_confirmed(path: Path) -> list[tuple[str, str]]:
    """Vrátí [(a5e, datasheet_rel)] pro řádky se status == 'confirmed'."""
    pairs: list[tuple[str, str]] = []
    for line in _read_text(path).splitlines():
        if not line.lstrip().startswith("| A5E"):
            continue
        cells = [c.strip() for c in line.split("|")]
        # cells[0]='' ; [1]=a5e ; [2]=komponenta ; [3]=datasheet ; [4]=status ; ...
        if len(cells) < 5:
            continue
        a5e, datasheet, status = cells[1], cells[3], cells[4]
        if status.lower() == "confirmed" and a5e.startswith("A5E") and datasheet:
            pairs.append((a5e, datasheet))
    return pairs


def _yaml_quote(text: str) -> str:
    """Bezpečný double-quoted YAML skalár (odstraní náhradní/řídicí znaky)."""
    clean = "".join(ch for ch in text if ch >= " " and ch != "\ufffd")
    return '"' + clean.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_workspaces_yaml(
    groups: dict[str, tuple[str, list[str]]],
) -> str:
    """groups: key -> (label, [filenames]) -> YAML blok 'workspaces:'."""
    lines = ["workspaces:"]
    for key in sorted(groups):
        label, files = groups[key]
        lines.append(f"  {key}:")
        lines.append(f"    label: {_yaml_quote(label)}")
        lines.append("    match:")
        for name in files:
            lines.append(f"      - {_yaml_quote(name)}")
    return "\n".join(lines) + "\n"


def stage_hardlinks(files: list[Path], staging: Path) -> None:
    """Čistý staging: smaže existující .pdf a vytvoří hardlinky (bez kopií)."""
    staging.mkdir(parents=True, exist_ok=True)
    for old in staging.glob("*.pdf"):
        old.unlink()
    for src in files:
        dst = staging / src.name
        if dst.exists():
            dst.unlink()
        os.link(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(description="Staging + per-component SpecPack build/index.")
    parser.add_argument("--partlist", type=Path, default=DEFAULT_PARTLIST)
    parser.add_argument("--pairing", type=Path, default=None,
                        help="datasheet_pairing.md. Výchozí: vedle Partlistu.")
    parser.add_argument("--components", type=Path, default=DEFAULT_COMPONENTS)
    parser.add_argument("--staging", type=Path, default=DEFAULT_STAGING)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--base-config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--out-config", type=Path, default=None,
                        help="Vygenerovaný config. Výchozí: vedle Partlistu (specpack.generated.yml).")
    parser.add_argument("--specpack", default=None)
    parser.add_argument("--full", action="store_true", help="Plný rebuild (bez --incremental).")
    parser.add_argument("--no-build", action="store_true", help="Jen staging + config.")
    parser.add_argument("--no-index", action="store_true", help="Přeskočit indexaci.")
    args = parser.parse_args()

    pairing = args.pairing or (args.partlist.parent / "datasheet_pairing.md")
    for p in (args.partlist, pairing, args.base_config):
        if not p.exists():
            sys.exit(f"CHYBA: soubor neexistuje: {p}")
    if not args.components.exists():
        sys.exit(f"CHYBA: složka Components neexistuje: {args.components}")

    # 1) klíče komponent z Partlistu
    comps = {c.a5e: c for c in aggregate_components(parse_partlist(_read_text(args.partlist)))}

    # 2) confirmed páry
    pairs = parse_pairing_confirmed(pairing)
    if not pairs:
        sys.exit("CHYBA: v párovacím souboru nejsou žádné 'confirmed' řádky.")

    # 3) seskupit per komponentu, ověřit existenci PDF
    groups: dict[str, tuple[str, list[str]]] = {}
    src_files: list[Path] = []
    missing: list[str] = []
    for a5e, rel in pairs:
        comp = comps.get(a5e)
        if comp is None:
            print(f"  ! přeskočeno (A5E není v Partlistu): {a5e} -> {rel}", flush=True)
            continue
        src = args.components / rel
        if not src.exists():
            missing.append(rel)
            continue
        label, files = groups.setdefault(comp.key, (comp.comment, []))
        if src.name not in files:
            files.append(src.name)
        src_files.append(src)
    if missing:
        sys.exit("CHYBA: chybí PDF:\n  " + "\n  ".join(missing))

    # 4) staging (hardlinky) + config
    stage_hardlinks(src_files, args.staging)
    out_config = args.out_config or (args.partlist.parent / "specpack.generated.yml")
    base_text = args.base_config.read_text(encoding="utf-8").rstrip() + "\n\n"
    out_config.write_text(base_text + build_workspaces_yaml(groups), encoding="utf-8")

    print(f"Potvrzených párů:  {len(pairs)}")
    print(f"Komponent (ws):    {len(groups)}")
    print(f"PDF hardlinků:     {len(src_files)} -> {args.staging}")
    print(f"Config:            {out_config}")

    if args.no_build:
        print("\nHOTOVO (jen staging + config).")
        return

    # 5) build + index
    specpack = resolve_specpack(args.specpack)
    env = dict(os.environ)
    env["PYMUPDF_MESSAGE"] = "fd:2"
    build_cmd = [specpack, "build", str(args.staging), "--workspaces",
                 "--config", str(out_config), "--out", str(args.root)]
    if not args.full:
        build_cmd.append("--incremental")
    run(build_cmd, env)
    if not args.no_index:
        run([specpack, "index", str(args.root), "--workspaces"], env)

    print("\nHOTOVO. Per-komponentní workspaces jsou v:", args.root, flush=True)


if __name__ == "__main__":
    main()
