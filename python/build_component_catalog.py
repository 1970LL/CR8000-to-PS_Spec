"""Deterministický krok: Partlist -> mapovací tabulka + katalog komponent (bez LLM).

Načte Partlist (Siemens Testway BOM), sloučí řádky na unikátní komponenty per A5E,
přiřadí deterministický klíč ``A5E__SLUG(COMMENT)`` a vypíše markdown katalog vedle
Partlistu (``component_catalog.md``).

Volitelně navrhne párování s existujícími PDF datasheety (substring MPN v názvu
souboru). Návrh je vždy jen podnět k **HITL verifikaci** — nikdy se nebere jako fakt
(no-guessing). Nepárované PDF i nepárované komponenty se vypíšou zvlášť.

Použití:
    python build_component_catalog.py
    python build_component_catalog.py --partlist <cesta> --components <dir> --out <soubor>
    python build_component_catalog.py --no-propose

Viz python/parse_partlist.py a diskuzi o pojmenování katalogu datasheetů.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_partlist import Component, aggregate_components, parse_partlist  # noqa: E402

# --- Výchozí cesty (lze přepsat argumenty) --------------------------------------
_PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_PARTLIST = _PROJECT / "Data" / "MCP1x10" / "20260825" / "Partlist_Test.txt"
DEFAULT_COMPONENTS = _PROJECT / "Data" / "MCP1x10" / "Components"


def _norm(text: str) -> str:
    """Normalizace pro fuzzy match MPN <-> název souboru: malá písmena, jen alfanum."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def index_pdfs(components_dir: Path) -> list[tuple[str, Path]]:
    """Rekurzivně najde PDF a vrátí (normalizovaný stem, cesta)."""
    if not components_dir.exists():
        return []
    return [(_norm(pdf.stem), pdf) for pdf in sorted(components_dir.rglob("*.pdf"))]


def propose_datasheets(
    a5e: str, mpn: str, pdf_index: list[tuple[str, Path]]
) -> list[tuple[Path, bool]]:
    """Návrh PDF pro komponentu. Vrací (cesta, strong).

    - strong=True: A5E je přímo v názvu souboru (exaktní, autoritativní).
    - strong=False: MPN je podřetězcem názvu souboru nebo naopak (>=5 znaků) — jen návrh.
    """
    a = _norm(a5e)
    m = _norm(mpn)
    hits: list[tuple[Path, bool]] = []
    for stem_norm, pdf in pdf_index:
        if a and a in stem_norm:
            hits.append((pdf, True))
        elif len(m) >= 4 and (m in stem_norm or (len(stem_norm) >= 5 and stem_norm in m)):
            hits.append((pdf, False))
    return hits


def _refdes_sample(refdes: list[str], limit: int = 4) -> str:
    if not refdes:
        return ""
    shown = refdes[:limit]
    suffix = f" …(+{len(refdes) - limit})" if len(refdes) > limit else ""
    return ", ".join(shown) + suffix


def _cell(text: str) -> str:
    """Escapuje '|' pro markdown tabulku, odstraní náhradní znaky a prázdné na '—'."""
    text = (text or "").replace("\ufffd", "").replace("|", "\\|").strip()
    return text or "—"


def build_catalog_md(
    components: list[Component],
    proposals: dict[str, list[tuple[Path, bool]]],
    components_dir: Path,
    partlist_path: Path,
) -> str:
    """Sestaví markdown katalog + sekci nepárovaných PDF."""
    lines: list[str] = []
    lines.append("# Katalog komponent — mapa A5E → klíč → datasheet")
    lines.append("")
    lines.append(f"> Zdroj: `{partlist_path.name}`. Vygenerováno deterministicky (bez LLM).")
    lines.append("> Sloupec **datasheets**: `✓` = A5E v názvu souboru (silná shoda), "
                 "`?` = návrh dle MPN (HITL verifikace).")
    lines.append("")
    lines.append("| key | a5e | mpn | kind | comment | qty | refdes | datasheets |")
    lines.append("|---|---|---|---|---|---:|---|---|")

    proposed_pdfs: set[Path] = set()
    for c in components:
        ds = proposals.get(c.a5e, [])
        proposed_pdfs.update(p for p, _ in ds)
        ds_cell = "; ".join(
            f"{p.name} {'✓' if strong else '`?`'}" for p, strong in ds
        ) if ds else "—"
        lines.append(
            "| " + " | ".join(
                [
                    _cell(c.key),
                    _cell(c.a5e),
                    _cell(c.mpn),
                    _cell(c.kind),
                    _cell(c.comment),
                    str(c.qty),
                    _cell(_refdes_sample(c.refdes)),
                    _cell(ds_cell),
                ]
            ) + " |"
        )

    # Nepárovaná PDF (existují na disku, ale žádný návrh je nepřiřadil)
    all_pdfs = [p for _, p in index_pdfs(components_dir)]
    unmatched = [p for p in all_pdfs if p not in proposed_pdfs]
    lines.append("")
    lines.append("## Nepárovaná PDF (k ručnímu přiřazení A5E)")
    lines.append("")
    if unmatched:
        for p in unmatched:
            rel = p.relative_to(components_dir) if components_dir in p.parents else p.name
            lines.append(f"- `{rel}`")
    else:
        lines.append("_(žádná)_")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Partlist -> katalog komponent (bez LLM).")
    parser.add_argument("--partlist", type=Path, default=DEFAULT_PARTLIST,
                        help=f"Vstupní Partlist. Výchozí: {DEFAULT_PARTLIST}")
    parser.add_argument("--components", type=Path, default=DEFAULT_COMPONENTS,
                        help=f"Složka s PDF datasheety (pro návrh párování). Výchozí: {DEFAULT_COMPONENTS}")
    parser.add_argument("--out", type=Path, default=None,
                        help="Výstupní markdown. Výchozí: component_catalog.md vedle Partlistu.")
    parser.add_argument("--no-propose", action="store_true",
                        help="Nenavrhovat párování s PDF.")
    args = parser.parse_args()

    if not args.partlist.exists():
        sys.exit(f"CHYBA: Partlist neexistuje: {args.partlist}")

    raw = args.partlist.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp1252", errors="replace")
    rows = parse_partlist(text)
    components = aggregate_components(rows)

    proposals: dict[str, list[tuple[Path, bool]]] = {}
    if not args.no_propose:
        pdf_index = index_pdfs(args.components)
        for c in components:
            hits = propose_datasheets(c.a5e, c.mpn, pdf_index)
            if hits:
                proposals[c.a5e] = hits

    out_path = args.out or (args.partlist.parent / "component_catalog.md")
    md = build_catalog_md(components, proposals, args.components, args.partlist)
    out_path.write_text(md, encoding="utf-8")

    n_ds = sum(len(v) for v in proposals.values())
    print(f"Řádků Partlistu:      {len(rows)}")
    print(f"Unikátních komponent: {len(components)}")
    print(f"Komponent s návrhem:  {len(proposals)} (celkem {n_ds} PDF návrhů)")
    print(f"Katalog zapsán:       {out_path}")


if __name__ == "__main__":
    main()
