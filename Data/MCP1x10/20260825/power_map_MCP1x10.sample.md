# power_map — MCP1x10 (UKÁZKA formátu: Markdown)

> Ukázka pro rozhodnutí formátu. 3 reálné záznamy z ISCF/Partlist.
> `ds_*` sloupce se plní až v kroku 3 (datasheety) — zde záměrně z části prázdné.
> Legenda: `power_state` ✅ = počítá se / ⛔ = zanedbatelné; `check` prázdné = OK / ⚠️ = nesoulad.

| check | power_state | rail | rail_v | refdes | pin | a5e | type | item | value | tolerance | voltage | ds_v_min | ds_v_max | ds_curr_max | ds_curr_typ | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | ✅ | P3V3 | 3.3 | D1202 | 8:VCC | A5E00063809 | EEPROM2Kx8ser. | IC_EEPROM_2Kbitx8_10ms_SOP8 | | | | | | | | (ds pending) |
| | ✅ | P3V3 | 3.3 | D9 | 20:VCC | A5E56410869 | 74LV8T541 | IC_INTERFACE_74LV8T541_1.65:5.5V_VSSOP- | | | | | | | | (ds pending) |
| ⚠️ | ✅ | VDD2 | | D8 | G2:7 | A5E56245815 | | IC_DDR4_128MB_x16_+95°C_BGA_200 | | | | | | | | rail_v neznámé → dotaz na uživatele |

## Poznámky k záznamům
- **D1202 / D9** — `power_supply` v ISCF `VCC=P3V3` odpovídá railu `P3V3` (křížová kontrola OK).
- **D8 (DDR4)** — multi-rail součástka (`VDD1/VDD2/VDDQ`), zde řádek pro rail `VDD2`.
  `rail_v` nelze dekódovat z názvu ani konvence → `⚠️` a dotaz na uživatele.
  `item` má opravenou diakritiku: `+95A??C` → `+95°C`. `type` je v BOM prázdný (OK).

## Sumy po railech (doplní krok 5)
| rail | rail_v | sum ds_curr_max [mA] | sum ds_curr_typ [mA] |
|---|---|---|---|
| P3V3 | 3.3 | (TBD) | (TBD) |
| VDD2 | (TBD) | (TBD) | (TBD) |
