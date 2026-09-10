"""Sestavení power_map: spojení ISCF + Partlist dle RefDes + křížová kontrola railů.

Krok 1 (Description.md kap. 4, 7, 12): pro každou kombinaci (RefDes, Rail) v ``BEGIN_POWER``
dohledá atributy z ``BEGIN_COMPPROPS`` (křížová kontrola railu vůči ``power_supply``) a
z Partlistu (dle RefDes), a serializuje výsledek do editovatelného HTML (formát dle
``power_map_MCP1x10.sample.html``). Je-li součástka na jednom railu připojena víc piny
(např. víc VCC pinů), sloučí se do jedné buňky ``pin`` (jeden pin na řádek buňky).

``power_state`` (✅/⛔/uzel) doplní automaticky ``power_filter.py`` (kap. 6, konfigurovatelné
— lze vypnout příznakem ``--no-filter``). Rail_v (dekodér, kap. 5) a ds_* (datasheety,
kap. 8-9) jsou stuby navazujících kroků — zde zůstávají prázdné, doplní je
``rail_decode.py`` / datasheet agent v dalších průchodech nad stejným souborem (diff
kap. 6, uchová ruční editace uživatele).

Použití:
    python build_power_map.py
    python build_power_map.py --iscf <cesta> --partlist <cesta> --out <soubor>

Viz python/parse_iscf.py, python/parse_partlist.py a Description.md.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from dataclasses import dataclass, fields
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_iscf import CompProps, Pin, parse_compprops, parse_power  # noqa: E402
from parse_partlist import PartRow, parse_partlist  # noqa: E402
from power_filter import NODE, PASS, SKIP, FilterConfig, apply_power_filter  # noqa: E402
from rail_decode import apply_rail_decode  # noqa: E402

# --- Výchozí cesty (lze přepsat argumenty) --------------------------------------
_PROJECT = Path(__file__).resolve().parent.parent
DEFAULT_ISCF = _PROJECT / "Data" / "MCP1x10" / "20260825" / "ISCF.txt"
DEFAULT_PARTLIST = _PROJECT / "Data" / "MCP1x10" / "20260825" / "Partlist_Test.txt"
DEFAULT_PROJECT_NAME = "MCP1x10"

_WARN = "⚠️"


@dataclass
class PowerMapRow:
    """Jeden záznam power_map (kombinace RefDes+Rail) — sloupce dle Description.md kap. 4.1.

    ``pin`` může obsahovat víc pinů téže součástky na stejném railu, oddělených '\n'
    (v HTML se serializují jako ``<br>`` — jeden pin na řádek buňky).
    """

    check: str
    power_state: str
    rail: str
    rail_v: str
    refdes: str
    pin: str
    a5e: str
    type: str
    item: str
    value: str
    tolerance: str
    voltage: str
    ds_v_min: str = ""
    ds_v_max: str = ""
    ds_curr_max: str = ""
    ds_curr_typ: str = ""
    source: str = ""


def _refdes_sort_key(refdes: str) -> tuple[str, int, str]:
    """Přirozené řazení RefDes: ``C2`` před ``C10`` (prefix, číslo, zbytek)."""
    m = re.match(r"([A-Za-z]*)(\d*)(.*)", refdes or "")
    prefix, num, rest = m.groups() if m else ("", "", refdes or "")
    return (prefix.upper(), int(num) if num else -1, rest)


def partlist_by_refdes(rows: list[PartRow]) -> dict[str, PartRow]:
    """Partlist řádky -> dict dle RefDes (klíč pro spojení s ISCF, kap. 2.2)."""
    return {r.refdes: r for r in rows if r.refdes}


def _rail_check(rail: str, cp: CompProps | None) -> str:
    """Křížová kontrola railu vůči ``power_supply`` (kap. 7). Prázdné/chybějící = OK."""
    if cp is None or not cp.power_supply:
        return ""
    return "" if rail in cp.power_supply.values() else _WARN


def _pin_label(p: Pin) -> str:
    return f"{p.pin}:{p.pin_label}" if p.pin_label else p.pin


def build_power_map(
    iscf_power: dict[str, list[Pin]],
    compprops: dict[str, CompProps],
    partlist: dict[str, PartRow],
) -> list[PowerMapRow]:
    """Vrátí seznam záznamů (RefDes, Rail) s dohledanými atributy z COMPPROPS+Partlist.

    Víc pinů téže součástky na stejném railu se sloučí do jednoho řádku (buňka ``pin``
    = piny oddělené '\n', jeden na řádek).
    """
    rows: list[PowerMapRow] = []
    for rail, pins in iscf_power.items():
        by_refdes: dict[str, list[Pin]] = {}
        for p in pins:
            by_refdes.setdefault(p.refdes, []).append(p)
        for refdes in sorted(by_refdes, key=_refdes_sort_key):
            group = by_refdes[refdes]
            cp = compprops.get(refdes)
            pr = partlist.get(refdes)
            rows.append(
                PowerMapRow(
                    check=_rail_check(rail, cp),
                    power_state="",
                    rail=rail,
                    rail_v="",
                    refdes=refdes,
                    pin="\n".join(_pin_label(p) for p in group),
                    a5e=pr.a5e if pr else "",
                    type=pr.type if pr else "",
                    item=pr.comment if pr else "",
                    value=pr.value if pr else "",
                    tolerance=pr.tolerance if pr else "",
                    voltage=pr.voltage if pr else "",
                )
            )
    return rows


# --- HTML serializace (formát dle power_map_MCP1x10.sample.html) ---------------------

_COLUMNS = [f.name for f in fields(PowerMapRow)]

_STYLE = """\
  :root { font-family: Segoe UI, Arial, sans-serif; }
  body { margin: 1rem; color: #1b1b1b; }
  h1 { font-size: 1.2rem; }
  .legend { font-size: .85rem; color: #444; margin-bottom: .5rem; }
  .toolbar { margin: .5rem 0 1rem; display: flex; gap: .5rem; flex-wrap: wrap; }
  button { padding: .4rem .8rem; cursor: pointer; }
  table { border-collapse: collapse; width: 100%; font-size: .82rem; }
  th, td { border: 1px solid #bbb; padding: .25rem .4rem; text-align: left; vertical-align: top; }
  th { background: #f0f3f7; position: sticky; top: 0; }
  td[contenteditable="true"]:focus { outline: 2px solid #3a7afe; background: #eef4ff; }
  tr:nth-child(even) td { background: #fafbfc; }
  .warn { background: #fff3cd !important; }
  .skip { color: #999; }
  body.hide-skip tr.skip { display: none; }
  caption { text-align: left; font-weight: 600; margin: 1rem 0 .3rem; }
"""

_SCRIPT = """\
  // Všechny datové buňky jsou editovatelné.
  function makeEditable() {
    document.querySelectorAll('tbody td').forEach(td => td.contentEditable = 'true');
  }
  makeEditable();

  document.getElementById('addRow').addEventListener('click', () => {
    const tb = document.querySelector('#pm tbody');
    const cols = document.querySelectorAll('#pm thead th').length;
    const tr = document.createElement('tr');
    for (let i = 0; i < cols; i++) { const td = document.createElement('td'); td.contentEditable = 'true'; tr.appendChild(td); }
    tb.appendChild(tr);
  });

  document.getElementById('toggleSkip').addEventListener('click', (e) => {
    document.body.classList.toggle('hide-skip');
    e.target.textContent = document.body.classList.contains('hide-skip') ? '👁️ Zobrazit ⛔' : '🙈 Skrýt ⛔';
  });

  function currentHTML() {
    return '<!DOCTYPE html>\\n' + document.documentElement.outerHTML;
  }

  // Uložení zpět do souboru přes File System Access API (Chrome). Fallback = stažení.
  let fileHandle = null;
  document.getElementById('save').addEventListener('click', async () => {
    try {
      if (!fileHandle) {
        fileHandle = await window.showSaveFilePicker({
          suggestedName: 'power_map_%(project)s.html',
          types: [{ description: 'HTML', accept: { 'text/html': ['.html'] } }]
        });
      }
      const w = await fileHandle.createWritable();
      await w.write(currentHTML());
      await w.close();
      alert('Uloženo.');
    } catch (e) { alert('Uložení zrušeno nebo nepodporováno: ' + e.message); }
  });

  document.getElementById('download').addEventListener('click', () => {
    const blob = new Blob([currentHTML()], { type: 'text/html' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'power_map_%(project)s.html';
    a.click();
    URL.revokeObjectURL(a.href);
  });
"""


def _esc(value: str) -> str:
    return html.escape(value or "", quote=False)


def _cell_html(col: str, value: str) -> str:
    esc = _esc(value)
    if col == "pin":
        esc = esc.replace("\n", "<br>")  # víc pinů téže součástky na stejném railu = víc řádků buňky
    return f"<td>{esc}</td>"


def _row_html(row: PowerMapRow) -> str:
    classes = []
    if row.check:
        classes.append("warn")
    if row.power_state == SKIP:
        classes.append("skip")
    tr_class = f' class="{" ".join(classes)}"' if classes else ""
    cells = "".join(_cell_html(col, getattr(row, col)) for col in _COLUMNS)
    return f"      <tr{tr_class}>\n        {cells}\n      </tr>"


def build_html(rows: list[PowerMapRow], project: str) -> str:
    """Sestaví editovatelné HTML (formát dle ``power_map_MCP1x10.sample.html``)."""
    header_cells = "".join(f"<th>{col}</th>" for col in _COLUMNS)
    body = "\n".join(_row_html(r) for r in rows)

    # Totals: unikátní raily v pořadí prvního výskytu (sumy doplní krok 5).
    seen: list[str] = []
    for r in rows:
        if r.rail not in seen:
            seen.append(r.rail)
    totals_body = "\n".join(
        f"      <tr><td>{_esc(rail)}</td><td></td><td></td><td></td></tr>" for rail in seen
    )

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>power_map — {project}</title>
<style>
{_STYLE}</style>
</head>
<body>
  <h1>power_map — {project}</h1>
  <div class="legend">
    Buňky lze přímo přepisovat (klikni a piš). <b>power_state</b>: ✅ počítá se / ⛔ zanedbatelné /
    <i>uzel</i> blok toku energie (LDO/DC-DC, pojistky, feritové perly…, řeší power_tree).
    <b>check</b>: prázdné = OK / ⚠️ nesoulad. <code>ds_*</code> se plní v kroku 3 (datasheety).
  </div>
  <div class="toolbar">
    <button id="save">💾 Uložit (Chrome File System)</button>
    <button id="download">⬇️ Stáhnout kopii</button>
    <button id="addRow">➕ Přidat řádek</button>
    <button id="toggleSkip">🙈 Skrýt ⛔</button>
  </div>

  <table id="pm">
    <thead>
      <tr>{header_cells}</tr>
    </thead>
    <tbody>
{body}
    </tbody>
  </table>

  <table id="totals">
    <caption>Sumy po railech (doplní krok 5)</caption>
    <thead>
      <tr><th>rail</th><th>rail_v</th><th>sum ds_curr_max [mA]</th><th>sum ds_curr_typ [mA]</th></tr>
    </thead>
    <tbody>
{totals_body}
    </tbody>
  </table>

<script>
{_SCRIPT % {"project": project}}</script>
</body>
</html>
"""


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description="ISCF + Partlist -> power_map (HTML).")
    parser.add_argument("--iscf", type=Path, default=DEFAULT_ISCF,
                        help=f"Vstupní ISCF. Výchozí: {DEFAULT_ISCF}")
    parser.add_argument("--partlist", type=Path, default=DEFAULT_PARTLIST,
                        help=f"Vstupní Partlist. Výchozí: {DEFAULT_PARTLIST}")
    parser.add_argument("--project", type=str, default=DEFAULT_PROJECT_NAME,
                        help=f"Jméno projektu (pro název souboru/titulek). Výchozí: {DEFAULT_PROJECT_NAME}")
    parser.add_argument("--out", type=Path, default=None,
                        help="Výstupní HTML. Výchozí: power_map_<project>.html vedle ISCF.")
    parser.add_argument("--no-filter", action="store_true",
                        help="Vypnout inteligentní filtr (kap. 6) — power_state zůstane prázdné/✅.")
    args = parser.parse_args()

    if not args.iscf.exists():
        sys.exit(f"CHYBA: ISCF neexistuje: {args.iscf}")
    if not args.partlist.exists():
        sys.exit(f"CHYBA: Partlist neexistuje: {args.partlist}")

    iscf_text = _read_text(args.iscf)
    compprops = parse_compprops(iscf_text)
    power = parse_power(iscf_text)
    partlist = partlist_by_refdes(parse_partlist(_read_text(args.partlist)))

    rows = build_power_map(power, compprops, partlist)
    apply_power_filter(rows, compprops, FilterConfig(enabled=not args.no_filter))
    apply_rail_decode(rows)

    out_path = args.out or (args.iscf.parent / f"power_map_{args.project}.html")
    out_path.write_text(build_html(rows, args.project), encoding="utf-8")

    n_warn = sum(1 for r in rows if r.check)
    n_pass = sum(1 for r in rows if r.power_state == PASS)
    n_skip = sum(1 for r in rows if r.power_state == SKIP)
    n_node = sum(1 for r in rows if r.power_state == NODE)
    rails_decoded = {r.rail for r in rows if r.rail_v}
    rails_unresolved = sorted({r.rail for r in rows if not r.rail_v})
    print(f"Railů:           {len(power)}")
    print(f"Záznamů (řádků): {len(rows)}")
    print(f"⚠️ nesoulad:     {n_warn}")
    print(f"✅ PASS / ⛔ SKIP / uzel NODE: {n_pass} / {n_skip} / {n_node}")
    print(f"rail_v dekódováno konvencí: {len(rails_decoded)} / {len(power)} railů")
    if rails_unresolved:
        print(f"rail_v nerozhodnuto (nutné trasování/dotaz): {', '.join(rails_unresolved)}")
    print(f"power_map zapsán: {out_path}")


if __name__ == "__main__":
    main()
