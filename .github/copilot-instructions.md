# Instrukce projektu CR8000-to-PS_Spec

Kontext: nástroj, který z podkladů CR8000 (ISCF + Partlist) sestaví mapu napájecí soustavy,
dopočítá spotřeby po railech a vygeneruje blokové schéma. Detailní zadání viz `Description.md`.

## Zásady
1. **Source of truth:** editace uživatele má vždy přednost před výpočtem AI.
2. **No guessing:** pokud výstup není deterministický, systém nehádá — navrhne hodnotu + metodiku
   a vyžádá si verifikaci/doplnění od uživatele.
3. **Offline:** vyhledávání na internetu není povoleno; zdrojem jsou pouze dodané podklady a datasheety.

## Konvence
- Dokumentace a komunikace s uživatelem: **česky**. Kód a identifikátory: **anglicky**.
- Python 3.11: `C:\Users\z003z5xd\AppData\Local\Programs\Python\Python311\`.
- Deterministické kroky (parsing, křížové kontroly, sumy) dělá Python; „měkké" úlohy
  (datasheety, návrhy proudů) dělá agent + HITL.
- Výstupy projektu se ukládají vedle zdrojových dat: `Data/<projekt>/<datum>/`.
- Cache datasheetů je globální: `Data/components_data.md`.

## Human-in-the-loop
Kontrolní body: po preprocessing -A- (filtr/diff), po preprocessing -B- (verifikace navržených
hodnot) a před generováním schématu. AI navrhuje, uživatel schvaluje/koriguje.
