# Párování datasheet ↔ A5E (HITL source of truth)

> Autoritativní přiřazení datasheetů ke komponentám. **Editace uživatele má přednost.**
> Tento soubor **přežije** regeneraci `component_catalog.md`. Cesty jsou relativní k
> `Data/MCP1x10/Components/`.
>
> **status:**
> - `confirmed` — potvrzeno (exaktní/silná shoda), připraveno ke stagingu.
> - `proposed` — návrh AI, čeká na tvé potvrzení (přepiš na `confirmed` / `rejected`).
> - `rejected` — nepárovat.
>
> Jedna komponenta může mít **více řádků** (víc datasheetů — např. procesor).

## Potvrzené / navržené páry

| a5e | komponenta (COMMENT) | datasheet | status | pozn. |
|---|---|---|---|---|
| A5E00157396 | IC_INTERFACE_74LVC244 | Logic/PHI_SN74LVC244A.pdf | confirmed | SN74LVC244A |
| A5E00524178 | IC_INTERFACE_26C32_RS422 | Interface/ds26c32at.pdf | confirmed | DS26C32AT |
| A5E01028306 | IC_GATE_74LVC1G08 | Logic/NEXP_74LVC1G08_Datasheet_20180116.pdf | confirmed | NXP 74LVC1G08 |
| A5E47026826 | IC_CryptoDevice_SE050A2 | Security Chip/A5E47026826_DB.pd.pdf | confirmed | A5E v názvu |
| A5E52100654 | IC_DRIVER_HIGH-SIDE_IPS8160HQ | High_Site_Switch/stm_ips8160hq.pdf | confirmed | ST IPS8160HQ |
| A5E56101679 | IC_LED-DRIVER_LP5860 | LED_Driver/lp5860.pdf | confirmed | TI LP5860 |
| A5E56151698 | IC_TEMPERATURSENSOR_TMP110 | Temp_Sensor/tmp110.pdf | confirmed | TI TMP110 |
| A5E56183142 | IC_SWITCH_MPF9453 | PMIC/PF9453.pdf | confirmed | NXP PF9453 (BOM „MPF") |
| A5E56410869 | IC_INTERFACE_74LV8T541 | Logic/sn74lv8t541.pdf | confirmed | TI SN74LV8T541 |
| A5E00439671 | IC_INTERFACE_74VHC125 | Logic/TII_SN74AHC125_Datasheet_RevO_202402.pdf | confirmed | náhrada VHC→AHC (schváleno) |
| A5E56245815 | IC_DDR4_128MB_x16 | RAM/W66BP6RB_W66CP2RQ_SDP_DDP_LPDDR4_LPDDR4X_combo_datasheet_A01-001_20250908.pdf | confirmed | COMMENT ponechán DDR4; DS je LPDDR4/X |
| A5E52725522 | Adjustable Current Limited Load Switch | Current_Limit_Switch/tps22950.pdf | confirmed | TI TPS22950 |
| A5E00063809 | IC_EEPROM_2Kbitx8_SOP8 | EEPROM/STD_m24c16-W.pdf | confirmed | M24C16 = 16Kbit = 2K×8 |
| A5E00769943 | IC_GATE_74AHC08 | Logic/TII_SN54AHC08_Datasheet_08222023.pdf | confirmed | SN54AHC08 = AHC08 (mil. grade) |
| A5E32187779 | IC_PERI_TUSB2046BI | Interface/tusb2046bi.pdf | confirmed | TUSB2046BVF = TUSB2046 (COMMENT „BI") |
| A5E56147206 | IC_INTERFACE_LAN96455S | Ethernet_Switch/LAN9645xS-Data-Sheet-DS00006066.pdf | confirmed | LAN9645**x**S, x=počet portů; 5S=5-port → DS pokrývá (ověřeno v PDF) |
| A5E56183582 | IC_NOR-xSPI_256Mbit/32Mbyte | Flash/QSPI-Flash/IS25LP(WP)256D.pdf | confirmed | IS25LP256 = 256Mbit NOR QSPI |
| A5E56183107 | IC_MCU_P_MIMX9121CVVXCAB | Processor/IMX91IEC.pdf | confirmed | i.MX91 datasheet |
| A5E56183107 | IC_MCU_P_MIMX9121CVVXCAB | Processor/IMX91RM.pdf | confirmed | i.MX91 reference manual |
| A5E56183107 | IC_MCU_P_MIMX9121CVVXCAB | Processor/imx91_HW_design_guide.pdf | confirmed | i.MX91 HW design guide |
| A5E54613593 | DIO_LED_MULTI_COLOUR_RGB | LED/DSE-0031501-23S-23B-R6GHBHC-A30-2A(HM)-V3.pdf | confirmed | RGB LED (49×, H601–H649); primární datasheet |
| A5E54613593 | DIO_LED_MULTI_COLOUR_RGB | LED/Everlight VBU product introduction_20240917.pdf | confirmed | druhý zdroj RGB LED (sloučeno do jednoho A5E) |

## Rozhodnuto (uživatel)

- **74VHC125** (`A5E00439671`) → `SN74AHC125` jako **náhrada** (VHC→AHC schváleno).
- **DDR4 128MB x16** (`A5E56245815`) → `W66…LPDDR4/X` (COMMENT ponechán DDR4).
- **Load switch** (`A5E52725522`) → `TPS22950`.

Krystaly/oscilátory (méně důležité pro power analýzu) — přiřaď jen pokud chceš:
`Oscilator/NDK_NZ2520SH_e.pdf`.

## Plánované / předpostavené v indexu (příští verze schématu)

> Tyto komponenty **nejsou v aktuálním Partlistu**, ale jsou **předpostavené v SpecPack indexu**
> (předpokládané použití v další verzi schématu). Ponechány záměrně jako příprava — při plném
> rebuildu z aktuálního Partlistu by z indexu vypadly.

| a5e | komponenta | datasheet | status |
|---|---|---|---|
| A5E43636907 | IC_OTHER_FUNCTION_MAX17526_TQFN20 | Input Filter/MAX17526A-MAX17526C_Rev3_2021-11.pdf | pre-built (future) |
| A5E33908377 | IC_SWITCH_TPS62097 | Buck/tps62097.pdf | pre-built (future) |
| A5E50483598 | IC_VREG_POS_LM76005RNPR | Buck/lm76005.pdf | pre-built (future) |
| A5E37725181 | REACTOR_470nH_5.9A | Inductor/A5E37725181_DB_WUEE_470nH_5.9A.pdf | pre-built (future) |
| A5E46604141 | REACTOR_470nH_4.8A | Inductor/A5E46604141_DB_SMI_201610CDMCDDS_470nH_4.8A.pdf | pre-built (future) |
| A5E47990248 | REACTOR_470nH_4.9A | Inductor/A5E47990248_DB_470nH_4.9A.pdf | pre-built (future) |
| A5E53512827 | REACTOR_470nH_4.5A_201612 | Inductor/A5E53512827_DB_MUT_DFE201612E_470nH_4.5A.pdf | pre-built (future) |

## Osiřelá PDF (future/historické — bez protějšku v Partlistu, NEpárovat)

Datasheety připravené k pozdějšímu použití nebo dříve zvažované a nakonec nepoužité:

> Pozn.: buck (`lm76005`, `tps62097`), induktory (`A5E37725181/46604141/47990248/53512827`) a
> `MAX17526` byly přesunuty do sekce **Plánované / předpostavené v indexu** (viz výše).

- `Ethernet_Switch/lan96459f … (managed mode) rev b.pdf` — LAN96459F, ne LAN96455S.
- `Ethernet_Switch/lan96459f … (unmanaged mode) rev b.pdf` — dtto.
- `quadraturencoder/stm/rm0490-…stm32c0…pdf` — kandidát MCU pro enkodér, neosazen.
- `quadraturencoder/stm/stm32c011f4.pdf` — dtto.
- `quadraturencoder/ti/mspm0c1105.pdf` — dtto.
- `RAM/43-46LQ16128A-AL.pdf` — nevybraný (zvolen W66 LPDDR4).
