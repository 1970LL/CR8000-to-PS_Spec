Ahoj, pojďme spolu interaktivně vytvořit projekt CR8000-to-PS_Spec.

Vytvoř soubor Description.md ve kterém vytvoříme zadání.

Cílem je vytvořit nástroj (v konečném stavu MCP Server nebo skill), který dokáže ze zadaných podkladů vytvořit mapu napájecí soustavy designovaného elektronického produktu, dopočítat spotřeby na jednotlivých hladinách (pro jejich správné dimenzování) v kaskádě až po vstupní napájecí hladinu která je nejčastěji 24V. Specifikace vstupního napětí je v dokumentu RBHW_a3_Version_12.1 v adresáři Documents.

Důležitou součástí projektu bude čtení datasheetů a dokumentů v formátu pdf, budeme potřebovat parser - SpecPack PDF jako MCP server. Tento není v prostředí VS kódu instalován, bude potřeba instalovat k globálnímu použití.

Hlavním vstupem ze systému CR8000 jsou dva textové soubory:

1. ISCF for Intel schematic review
testovací dokument \data\mcp1x10\20260825\iscf.txt
Důležitá sekce je na začátku označena: "BEGIN_POWER" a na a konci označena "END POWER". Tato sekce specifikuje napájecí nety (Raily) a k nim připojené komponenty (součástky) včetně připojených pinů těchto součástek.

2. Parts Lists (Testway)
testovací dokument \data\mcp1x10\20260825\Test_partlist.txt
Tento dokument je BOM (rozpiska materiálu): 
- ARTIKEL - definuje A5E číslo, jednoznačný identifikátor materiálu. Dle tohoto čísla je definován materiál v PLM systému TeamCenter.
- EPL - referenční značení ve schématu zapojení. Je třeba pro propojení s ISCF dokumentem
- TYPE - typ součástky, např. 74LVC244
- COMMENT - značení v TeamCenter např. IC_INTERFACE_74LVC244_1.65V-3.6V_TSSOP-2
-  Value - hodnota, zejména u pasivních součástek - rezistorů, kondenzátorů. Může být obsažena v COMMENT.
- Tolerance - tolerance odporu, kapacity. Zejména u pasivních součástek. Také může být součástí COMMENT.
- Napětí - zejména u kondenátorů. Může být součástí COMMENT.

Pro nás budou důležité zejména první čtyři parametry, ale parsoval bych celý BOM, nevíme kdy se mohou informace hodit při dalším zpracování.

Tyto dokumenty vytvoří uživatel exportem v CR8000 Design Editor -> Tool -> Netlist Processor -> následně výběrem z menu Output Format. Není to práce AI.

Workflow:

1. Naparsovat vstupní dokumenty (Python v3), vytvořit editovatelný xml formát soubor power_map_xx (xx = jméno projektu např "MCP1x10"). Soubor uložit do stejného adresáře jako zdrojová data. Python v3 je v C:\Users\z003z5xd\AppData\Local\Programs\Python\Python311\

Vzor struktury
Check |Rail    |Rail_V  | RefDes |Pin   |A5E           |Type          |
      |P3V3    |3.3     | D1202  |8:VCC |A5E56245815   |              |

Item                                          |Value|Tolerance|
EEPROM2Kx8ser.IC_EEPROM_2Kbitx8_10ms_SOP8     |     |         |

Voltage|DS V_Range_min |DS V_Range_max |DS Curr_max |DS Curr_typ | 
       |1.8            |5              |2           |1           |       

RefDes = EPL (Partlist)
- Rail - extrahovat s ISCF (BEGIN_POWER/END POWER)
- Rail_V - hodnota napětí railu. Jednotka[V]. Většinou se jedná o definici přímo v názvu - P5, P12, P3V3, P0V85 - pak je extrakce jasná o 5, 12, 3.3, 0.85V. Jindy je specifikace složitější, např. NVCC_BBSM_P1V8, SNVS_P0V8, VDDIO_P1V8 ale stále obsahuje konvenci PxVy a je to 1.8, 0.8 a 1.8V. Pro nedefinované případy, jako např. VDDAH_PHY je možné ověřit jestli vedou na feritovou perlu, spínací prvek, odpor malé hodnoty atp. a následně na napájecí rail (v tomto případě P3V3) a odtud dekódovat hodnotu napětí. U railů kde není vazbu možno nalézt (nebo výsledek není deterministický), systém požádá uživatele o doplnění hladiny napájení. Např. VDD2, VDDQ.   
- Pin - extrahovat z ISCF, najít BEGIN POWER, naparsovat dle RefDes, extrahovat z příklad "D1202(8:VCC)" Domyslet křížovou kontrolu - v oddíle který začáná BEGIN_COMPPROS najít součástku dle RefDes, zkontrolovat propojení na správný rail. Příklad "D1202:A5E00063809,,,,,,,,,,104,VCC=P3V3;GND=GND". Některé součástky mají více napájecích railů, zde příklad LPDDR4 "D8:A5E56245815,,,,,,,,,,104,VDD1=VCC;VDD2=VCC;VDDQ=VCC;VSS=GND". Některé zde napájecí rail uvedený nemají. Není to chyba, jedná se o jiný způsob připojení ve schéma zapojení. Nesmí zde být rozpor např. "P3V3" vs. "P1V8".
- A5E = ARTIKEL, dohledat dle ReFDes v "Partlist_Test"
- Type = TYPE, dohledat dle ReFDes v "Partlist_Test" - může být prázdná hodnota
- Item = COMMENT, dohledat dle ReFDes v "Partlist_Test" - pozor na diakritiku a znakovou sadu. "IC_DDR4_128MB_x16_+95A  C_BGA_200" má být "IC_DDR4_128MB_x16_+95°C_BGA_200".
- Value, Tolerance, Voltage = Value, Tolerance, Voltage dohledat dle ReFDes v "Partlist_Test" - může být prázdná hodnota

Údaje doplněné v dalším kroku z datasheetů součástek:
- DS V_Range_min - minimální provozní napětí. Jednotka[V] 
- DS V_Range_max - maximální provozní napětí. Jednotka[V]
Bere se z "Operating conditions", nejdná se o "Absolute Maximum ratings". Možná bude potřeba zapojit AI na dohledání správných parametrů, uvidíme ze zpracování vzorových datasheetů. V případě, že neexistuje jistota o správnosti nalezených dat, uživatel na to musí být upozorněn - data verifikovat, nebo dohledat v datsheetech ručně.   
- DS Curr_max, DS Curr_typ - maximální a typický napájecí proud. Jednotka[mA]. Dohledat tento údaj nebude v některých případech snadné. V uvedeném příkladě byla zvolena max. hodnota z datasheetu pro 5V, přestože správněji by bylo použít derating pro uvedená napájení 1.8V a 5V. V tomto vzoru, byla zvolena zjednodušená strategie. Mnohdy je ale napájecí proud závislý na dalších podmínkách, výpočtu, frekvenci atp. Pokud není výstup deterministický, AI může navrhnout údaj + metodiku jak k němu došla, data však musí být verifikována uživatelem. Typ proud je pak derating dle konkrétních podmínek, zde v modelovém případě EEPROM by se jednalo o poměr stand by času k aktivnímu času (čtení/zápis), ale uživatel může poskytnout odhadnutý koeficient. AI navrhuje, uživatel schvaluje/koriguje v interaktivním dialogu.

- Pozor u součástek jako jsou LDO, DC/DC konvertory, spínače napájení (diskrétní i integrované), feritové perly, pojistky, rezistory "malé" hodnoty a konektory. Tyto součásti mohou mít vlastní spotřebu malou nebo žádnou, ale zátěž k nim může být připojena z jejich výstupu, nebo přímo (pokud se jedná o konektor). Tyto součástky (s výjimkou konektorů) mohou mít na straně vstupu i výstupu definovaný rail, ale na výstupu to není nutná podmínka - může zde být obecný Net. Pokud se jedná o konektor s externí záteží, musí dodat vstupní hodnoty uživatel. Data nejsou dostupná v podkladech. Doporučuji soubor Ext_loads.md. V případě nejasností nesmí systém hádat - musí vyzvat uživatele k objasnění problému nebo rozporu.

- spotřeba u LED dioda vyplývá z jejich typu (vlastního úbytku napětí), napájecí hladiny na které jsou připojeny a sériového rezistoru. LED jsou většinou připojeny na driver nebo OC tranzitor/fet.

2. Inteligentní preprocessing -A- 

- Inteligentní filtr - součástky které nespotřebovávají energii, nebo ji spotřebovávají jen v zanedbatelné míře. Typicky se jedná o blokovací kondenzátory, Pull-up odpory a podobně. Tyto součástky systém označí ⛔ a nebude je počítat do celkové spotřeby. Ostatní komponenty systém označí ✅ - do spotřeby budou započteny.  
- vytvořit parametry filtru, co bude zařazeno, co bude filtrováno. Možnost filtr zapnout/vypnout. Možnost vyfiltrované položky zobrazit/potlačit.
- kontrola a komparace s předchozí verzé dokumentu. Nutno domyslet. Účelem je zpracovat dif proti předchozí verzi a přenést položky které jsou beze změny.  
- výsledný výstupní soubor kontroluje/edituje uživatel a uloží k dalšímu zpracování. Editace uživatele je source of truth.


3. Parsing dat z datasheetů

- datasheety dodává uživatel do složky \data\mcp1x10\datasheets\...
- pro parsování bude využit SpecPack připojený jako MCP Server. Nutno implememntovat a zprovoznit. 
- vyhledávání na internetu není povoleno
- pokud systém nenajde potřebný datasheet upozorní uživatele, ten jej dodá
- datasheety mohou být roztříděny po skupinách v dalších podsložkách, jmenná konvence ani další pravidla nejsou zatím stanovena. V případě, že systém nebude funkční, lze konvenci např. dle A5E čísla zavézt.
- systém ukládá již naparsovaná data do souboru \data\components_data.md pro globální využití ve všech projektech. Do souboru uloží Siemens atributy - A5E číslo, Item, DS V_Range_min, DS V_Range_max, DS Curr_max, DS Curr_typ a dále jméno datasheetu, jeho revizi, datum vydání a paragraf, stranu nebo číslo tabulky, odkud byla data zdrojována. Před parsováním nového datasheetu systém ověří, není-li již součástka v souboru. Pokud ji nalezne, použijí se data ze souboru, parsování datasheetu se přeskočí.  

4. Inteligentní preprocessing -B-

- zkontrolovat, že Rail_V je v rozsahu DS V_Range_min a DS V_Range_max. Nesoulad/problém označit symbolem ⚠️ v položce check. 
- zkontrolovat vyplnění a konzistenci údajů
Systém upozorní na zjištěné problémy chybovým hlášením.

5. Vypočtění spotřeb

- jedná se o sumy DS Curr_max a DS Curr_typ pro jednotlivé Raily (napájecí hladiny)
- sumy systém uloží na konec souboru power_map_xx.

6. Vytvoření blokového schéma napájecí soustavy

- systém vytvoří blokové schéma napájecí soustavy jako editovatelné soubory Mermaid - power_tree_xx.drawio, power_tree_xx.mmd.
- logický směr toku energie zleva doprava, vlevo vstup, vpravo výstupy
- LDO, DC/DC konvertory, spínače napájení se označí jako blok s definováním vstupních a výstupních Railů jejich hodnot a sum proudů v těchto jednotlivých částech
- shodný přístup u feritových perel, pojistek, rezistorů "malé" hodnoty
- zvlášť označeny externí zátěže včetně RefDes konektorů
- do mapy zakreslit jako bloky všechny výrazné spotřebiče. Nastavitelná mez, default 30mA.

7. Vypočtení celkových energetických toků

- přepočítat toky proudů z výstupu bloků na jejich vstupy, zejména se to týká DC/DC (buck) konvertorů kde do  výpočtu vstpuje účinnost.
- doplnit tato data do blokového schématu

Role:

- vlastník projektu: human - Lubor
- AI role k diskuzi - rozdělit na architek + implementer, nebo zvládnout jedním průchodem?
- AI agentic system - definovat skils, agenty apod.