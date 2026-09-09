# Python moduly (Python 3.11)

Deterministické kroky workflow. **Zatím pouze stuby bez logiky** — implementace navazuje po
rozhodnutí formátu `power_map` (viz `Description.md` kap. 4 a 15).

| Modul | Krok | Odpovědnost |
|---|---|---|
| `parse_iscf.py` | 1 | parsing sekcí ISCF (`BEGIN_COMPPROPS`, `BEGIN_POWER`, …) |
| `parse_partlist.py` | 1 | parsing BOM (Testway), normalizace kódování/diakritiky |
| `build_power_map.py` | 1 | spojení dle RefDes + křížová kontrola railů → `power_map_xx` |
| `rail_decode.py` | 5 (kap.) | dekódování `rail_v` (konvence + trasování topologie) |
| `power_filter.py` | 2 | inteligentní filtr ✅/⛔ (dle `componentKind` + BOM) |
| `build_power_tree.py` | 6–7 | sumy, přepočet toků, generování Mermaid/draw.io |

Spouštění: `& "C:\Users\z003z5xd\AppData\Local\Programs\Python\Python311\python.exe" <modul>.py`

## SpecPack index datasheetů (mechanika, bez LLM)

Výchozí workflow je **per-komponenta**: 1 workspace = 1 A5E komponenta s čistým jménem
`A5E<num>__<SLUG(COMMENT)>`. Modul `build_datasheet_workspaces.py` je deterministický
krok (**bez LLM**), který:

1. načte klíče komponent z Partlistu (`parse_partlist`),
2. načte **confirmed** páry z `datasheet_pairing.md` (`a5e` → datasheet(y)),
3. vytvoří staging s **hardlinky** na potvrzená PDF (bez kopií; osiřelá/future PDF se nestagují),
4. vygeneruje SpecPack config s `workspaces:` sekcí (multi-doc komponenta = víc PDF → jeden workspace),
5. spustí `specpack build --workspaces` + `specpack index --workspaces` do sdíleného
   globálního rootu (`D:\Code\Tools\specPack\workspaces`).

**Spuštění přes VS Code task** (doporučeno): `Ctrl+Shift+P` → *Tasks: Run Task* →
- `SpecPack: Build & Index datasheets` — build + index,
- `SpecPack: Full rebuild datasheets` — plný rebuild (`--full`).

**Spuštění z terminálu:**
```powershell
$py = "C:\Users\z003z5xd\AppData\Local\Programs\Python\Python311\python.exe"
& $py python\build_datasheet_workspaces.py            # build + index
& $py python\build_datasheet_workspaces.py --full     # plný rebuild
& $py python\build_datasheet_workspaces.py --no-build # jen staging + config
```

Volitelné argumenty: `--partlist <cesta>`, `--pairing <cesta>`, `--components <dir>`,
`--staging <dir>`, `--root <dir>` (cíl indexu), `--base-config <yml>`, `--specpack <cesta>`.

Po doběhnutí je index dostupný přes MCP server `specpack` (viz `.vscode/mcp.json`)
a nástroje `spec_search` / `spec_context` / `spec_get`. MCP discovery skenuje root na
`**/specpack.db`; přejmenování/přesun složek se projeví až po **restartu** serveru.

> **DEPRECATED:** `build_specpack_index.py` (`specpack ... --per-doc`) byl per-**datasheet**
> a vyráběl ošklivá lit-number jména (JESD36, SLLS413, …). Nepoužívat pro nové běhy —
> zůstává jen kvůli sdíleným symbolům (`resolve_specpack`, `run`, výchozí cesty), které
> importuje nový driver.

## Katalog komponent (Partlist → mapa A5E → klíč → datasheet)

Modul `build_component_catalog.py` je deterministický krok (bez LLM), který z Partlistu
(Siemens Testway BOM) sloučí řádky na **unikátní komponenty per A5E** a přiřadí každé
stabilní klíč:

```
klíč = A5E<num>__<SLUG(COMMENT)>        # A5E nese unikátnost + řazení, COMMENT = lidský label
fallback: COMMENT prázdný -> SLUG(TYPE) -> holé A5E
```

SLUG normalizace: velká písmena, ne-`[A-Z0-9]` -> `_`, sloučení `_`, limit 48 znaků.
Klíč je vždy čistě ASCII a filesystem-safe (proto se použije jako název per-komponent
workspace SpecPacku místo auto-detekovaných doc-id).

Volitelně navrhne **párování s PDF** ve složce Components (parametr `--components`):
- `✓` = A5E je přímo v názvu souboru (exaktní, autoritativní),
- `?` = MPN je podřetězcem názvu (jen návrh, vyžaduje **HITL** verifikaci).

Nepárovaná PDF se vypíšou zvlášť k ručnímu přiřazení A5E.

**Spuštění přes VS Code task**: *Tasks: Run Task* → `Katalog: Partlist → component_catalog.md`.

**Spuštění z terminálu:**
```powershell
$py = "C:\Users\z003z5xd\AppData\Local\Programs\Python\Python311\python.exe"
& $py python\build_component_catalog.py                       # výchozí Partlist_Test
& $py python\build_component_catalog.py --partlist <cesta>    # jiný Partlist
& $py python\build_component_catalog.py --no-propose          # bez párování PDF
```

Výstup `component_catalog.md` se zapíše vedle Partlistu (`--out` přepisuje cíl).
Parser samá (`parse_partlist.py`) je znovupoužitelný: `parse_partlist(text)` → `PartRow`,
`aggregate_components(rows)` → unikátní `Component` per A5E.

