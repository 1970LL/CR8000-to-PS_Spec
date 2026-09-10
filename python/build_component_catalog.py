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
from parse_partlist import (  # noqa: E402
    Component,
    aggregate_components,
    function_type,
    parse_partlist,
    refdes_prefix,
)

# --- Výchozí cesty (lze přepsat argumenty) --------------------------------------
_PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_PARTLIST = _PROJECT / "Data" / "MCP1x10" / "20260825" / "Partlist_Test.txt"
DEFAULT_COMPONENTS = _PROJECT / "Data" / "MCP1x10" / "Components"
DEFAULT_PAIRING = _PROJECT / "Data" / "MCP1x10" / "20260825" / "datasheet_pairing.md"

# Pořadí skupin (prefix RefDes) pro řazení katalogu jako BOM dokumentu.
# HITL: uprav pořadí dle potřeby; neznámé prefixy jdou na konec.
BOM_ORDER: list[str] = [
    "R",   # rezistory
    "C",   # kondenzátory
    "V",   # diody, tranzistory (diskrétní polovodiče)
    "L",   # cívky / tlumivky
    "Z",   # filtry (EMI, feritové perly)
    "B",   # krystaly
    "G",   # oscilátory
    "D",   # digitální IO
    "N",   # analogové IO
    "U",   # optočleny
    "T",   # transformátory / měniče
    "K",   # relé
    "F",   # pojistky
    "S",   # spínače / kódovací přepínače
    "H",   # LED / žárovky
    "X",   # konektory
    "P",   # testpointy
    "W",   # antény
    "A",   # sestavy
    "Q",   # ostatní
]


def _component_prefix(c: Component) -> str:
    return refdes_prefix(c.refdes[0]) if c.refdes else ""


def _bom_index(prefix: str) -> int:
    try:
        return BOM_ORDER.index(prefix)
    except ValueError:
        return len(BOM_ORDER)


def _norm(text: str) -> str:
    """Normalizace pro fuzzy match MPN <-> název souboru: malá písmena, jen alfanum."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def index_pdfs(components_dir: Path) -> list[tuple[str, Path]]:
    """Rekurzivně najde PDF a vrátí (normalizovaný stem, cesta).

    Ignoruje složku ``Archive`` v libovolné úrovni (vyřazené / mimo scope PDF).
    """
    if not components_dir.exists():
        return []
    out: list[tuple[str, Path]] = []
    for pdf in sorted(components_dir.rglob("*.pdf")):
        rel_parts = pdf.relative_to(components_dir).parts
        if any(part.lower() == "archive" for part in rel_parts):
            continue
        out.append((_norm(pdf.stem), pdf))
    return out


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def load_pairing(path: Path) -> tuple[dict[str, list[tuple[str, str]]], set[str]]:
    """Načte ``datasheet_pairing.md`` (HITL source of truth).

    Vrací:
      - ``confirmed`` : a5e -> [(datasheet_rel, pozn.)] jen pro status ``confirmed*``.
      - ``known_rel`` : množina relativních cest datasheetů zmíněných v tabulkách
        (confirmed i pre-built/future), normalizovaná na lowercase s ``/``. Slouží
        k vyloučení z „Nepárovaná PDF".
    """
    confirmed: dict[str, list[tuple[str, str]]] = {}
    known: set[str] = set()
    if not path.exists():
        return confirmed, known
    for line in _read_text(path).splitlines():
        if not line.lstrip().startswith("| A5E"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5:
            continue
        a5e, datasheet, status = cells[1], cells[3], cells[4]
        note = cells[5] if len(cells) >= 6 else ""
        if not (a5e.startswith("A5E") and datasheet):
            continue
        known.add(datasheet.replace("\\", "/").lower())
        if status.lower().startswith("confirmed"):
            confirmed.setdefault(a5e, []).append((datasheet, note))
    return confirmed, known


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
    confirmed: dict[str, list[tuple[str, str]]],
    known_rel: set[str],
    components_dir: Path,
    partlist_path: Path,
    pairing_path: Path,
) -> str:
    """Sestaví markdown katalog (řazený dle Function Type) + sekci nepárovaných PDF.

    Datasheets sloupec: potvrzené páry z ``datasheet_pairing.md`` (✅, autoritativní) mají
    přednost; jinak heuristický návrh dle A5E (✓) / MPN (?). ``known_rel`` (datasheety
    zmíněné v párování, confirmed i pre-built) se vyloučí z „Nepárovaná".
    """
    lines: list[str] = []
    lines.append("# Katalog komponent — mapa A5E → klíč → datasheet")
    lines.append("")
    lines.append(f"> Zdroj: `{partlist_path.name}`. Vygenerováno deterministicky (bez LLM).")
    lines.append("> Řazeno dle **Function Type** (BOM pořadí, odvozeno z prefixu RefDes).")
    lines.append("> Sloupec **datasheets**: `✅` = potvrzeno v "
                 f"`{pairing_path.name}`; `✓` = A5E v názvu souboru; `?` = návrh dle MPN (HITL).")
    lines.append("")
    lines.append("| ft | key | a5e | mpn | kind | comment | qty | refdes | datasheets |")
    lines.append("|---|---|---|---|---|---|---:|---|---|")

    proposed_pdfs: set[Path] = set()
    components_sorted = sorted(
        components,
        key=lambda c: (
            _bom_index(_component_prefix(c)),
            function_type(c.refdes[0] if c.refdes else "")[0],
            c.comment.upper(),
            c.a5e,
        ),
    )
    for c in components_sorted:
        code, label = function_type(c.refdes[0] if c.refdes else "")
        ft_cell = f"{label} ({code})" if code != 999 else "?"
        conf = confirmed.get(c.a5e, [])
        if conf:
            ds_cell = "; ".join(f"{Path(rel).name} ✅" for rel, _ in conf)
        else:
            ds = proposals.get(c.a5e, [])
            proposed_pdfs.update(p for p, _ in ds)
            ds_cell = "; ".join(
                f"{p.name} {'✓' if strong else '`?`'}" for p, strong in ds
            ) if ds else "—"
        lines.append(
            "| " + " | ".join(
                [
                    _cell(ft_cell),
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

    # Nepárovaná PDF: na disku, ale nezmíněná v párování a bez heuristického návrhu.
    all_pdfs = [p for _, p in index_pdfs(components_dir)]
    unmatched: list[Path] = []
    for p in all_pdfs:
        rel = p.relative_to(components_dir) if components_dir in p.parents else Path(p.name)
        rel_norm = str(rel).replace("\\", "/").lower()
        if rel_norm in known_rel or p in proposed_pdfs:
            continue
        unmatched.append(p)
    lines.append("")
    lines.append("## Nepárovaná PDF (k ručnímu přiřazení A5E)")
    lines.append("")
    lines.append(f"> Vyloučeny datasheety potvrzené/plánované v `{pairing_path.name}`.")
    lines.append("")
    if unmatched:
        for p in unmatched:
            rel = p.relative_to(components_dir) if components_dir in p.parents else p.name
            lines.append(f"- `{rel}`")
    else:
        lines.append("_(žádná — vše přiřazeno v párování)_")
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
    parser.add_argument("--pairing", type=Path, default=None,
                        help="datasheet_pairing.md (potvrzené páry). Výchozí: vedle Partlistu.")
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

    pairing_path = args.pairing or (args.partlist.parent / "datasheet_pairing.md")
    confirmed, known_rel = load_pairing(pairing_path)

    proposals: dict[str, list[tuple[Path, bool]]] = {}
    if not args.no_propose:
        pdf_index = index_pdfs(args.components)
        for c in components:
            if c.a5e in confirmed:
                continue  # potvrzeno v párování → heuristiku nepotřebujeme
            hits = propose_datasheets(c.a5e, c.mpn, pdf_index)
            if hits:
                proposals[c.a5e] = hits

    out_path = args.out or (args.partlist.parent / "component_catalog.md")
    md = build_catalog_md(
        components, proposals, confirmed, known_rel, args.components, args.partlist, pairing_path
    )
    out_path.write_text(md, encoding="utf-8")

    n_ds = sum(len(v) for v in proposals.values())
    print(f"Řádků Partlistu:      {len(rows)}")
    print(f"Unikátních komponent: {len(components)}")
    print(f"Potvrzeno v párování: {len(confirmed)} komponent")
    print(f"Heuristických návrhů: {len(proposals)} (celkem {n_ds} PDF)")
    print(f"Katalog zapsán:       {out_path}")


if __name__ == "__main__":
    main()
