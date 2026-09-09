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
