# Backlog — CR8000-to-PS_Spec

> Nápady a vylepšení k pozdějšímu zpracování. Nejde o změny koncepce vyžadující okamžitý
> zásah. Řazeno dle témat, ne dle priority. Zdroj: průběžné HITL poznámky (Lubor).

---

## B1 — Check: dvoupólová součástka zkratovaná na jeden net

**Poznámka (2026-09-10):** `R58` má oba piny připojené na `P5` (ověřeno v ISCF:
`R58(1:1),R58(2:2)` v railu `P5`; sekce `BEGIN_COMPPINS`: `R58((1:1:::),(2:2:::))`).
To je **chyba ve schématu** — dvoupólová součástka (rezistor, kondenzátor, cívka, dioda,
feritová perla…) nemůže mít smysluplně oba póly na jednom netu (= zkrat / mrtvá součástka).

**Návrh:** deterministický `check` (⚠️) ve `build_power_map` nebo v samostatném konzistenčním
průchodu. Postavit mapu `pin → net` napříč `BEGIN_POWER` + `BEGIN_NETS` + `BEGIN_GROUND`;
pro součástky s právě 2 piny ověřit, že piny nejsou na stejném netu.

**Rozsah / pozor:**
- Omezit na dvoupólové třídy: `C` (kond.), `R` (rezistor), `L` (cívka), `V` (dioda —
  2 vývody), `Z` (filtr/ferit). Vyloučit hvězdicové body `WS` (propojky — spojení je záměr).
- Součástky s >2 piny (IC, konektory) tímto pravidlem neřešit.
- `0R` propojka se záměrně stejným netem na obou koncích je nesmyslná, ale neškodná — přesto
  spíš hlásit jako ⚠️ (pravděpodobně chyba návrhu).

**Náročnost:** nízká, deterministické, žádná změna koncepce.

---

## B2 — Check: pin ↔ hladina dle datasheetu

**Poznámka (2026-09-10):** z netlistu vyplyne, které piny jsou připojené na kterou hladinu
(rail). Bylo by účelné ověřit, že je to **správně dle datasheetu** (tj. napájecí pin očekává
danou hladinu).

**Zařazení do workflow:** krok **4 — Preprocessing -B- (kontrola konzistence)**, kde už
probíhá kontrola `rail_v ∈ ⟨ds_v_min, ds_v_max⟩`. Tento check jde o úroveň hlouběji
(pin-level, ne jen component-level).

**Dvě úrovně realizace (od levné k drahé):**
1. **Levná (bez datasheetu):** `pin_label` v ISCF často nese funkci pinu (`VCC`, `VDD1`,
   `VDD2`, `VDDQ`, `VDDIO_P1V8`…). Lze porovnat sémantiku `pin_label` vs. `rail_v` /
   název railu bez čtení PDF (např. label obsahující `1V8` na railu ≠ 1.8 V → ⚠️).
2. **Drahá (dle datasheetu):** vyžaduje strukturovanou tabulku pinů z datasheetu
   (pin → funkce → očekávaná hladina). Extrakce přes SpecPack je nejistá → **riziko
   „hádání"** (zásada č. 2). Realizovat jen tam, kde je pin tabulka spolehlivě čitelná,
   jinak nechat na HITL. AI navrhne, uživatel schválí.

**Náročnost:** úroveň 1 nízká–střední; úroveň 2 vysoká (závislá na kvalitě extrakce PDF).

---

## B3 — HTML: řazení tabulky dle sloupců

**Poznámka (2026-09-10):** možnost řadit `power_map` dle `check`, `power_state`, `refdes`,
`rail` (příp. dle všech sloupců, vzestupně/sestupně).

**Odpověď na dotaz „podporuje to HTML?":** ano. Client-side řazení přes vanilla JS —
klikací hlavičky sloupců, přepínání vzestupně/sestupně, žádná knihovna navíc. Kompatibilní
s `contenteditable` (řazení jen přeuspořádá DOM řádky).

**Návrh:**
- Klik na `<th>` → seřadí dle sloupce; druhý klik → obrátí směr (indikátor ▲/▼).
- Přirozené řazení RefDes (`C2` < `C10`) a numerické u `rail_v` / `ds_*`.
- **Pozor na grouping (B-grouping):** víceřádkové buňky `pin` (`<br>`) neovlivňují řazení
  (řadíme podle řádku = kombinace RefDes+Rail). OK.
- Volitelně: sekundární klíč (např. rail → refdes) — až po základní verzi.

**Náročnost:** nízká, čistě UI vrstva generovaného HTML, žádná změna dat ani koncepce.

---

## B4 — Grafický symbol pro `power_state = uzel`

**Poznámka (2026-09-10):** aktuálně se `uzel` zobrazuje jako prostý text (bez ikony jako
✅/⛔). Kosmetická záležitost — HITL potvrzeno, není urgentní. Možná se vyřeší samo při
implementaci `power_tree` (kap. 6-7), kde bude potřeba uzly vizuálně odlišit i jinde
(Mermaid/draw.io bloky). Než se do toho pustíme, zvážit jednotný symbol napříč `power_map`
i `power_tree` (např. 🔀 nebo 🔧) místo řešení zvlášť pro každý výstup.

**Náročnost:** velmi nízká (kosmetika), bez dopadu na data/logiku.

---

## Konvence backlogu
- ID `B<n>`, krátký titulek, poznámka s datem, návrh řešení, zařazení do workflow, náročnost.
- Po realizaci položku přesunout do repo paměti / `Description.md` a zde označit `~~hotovo~~`.
